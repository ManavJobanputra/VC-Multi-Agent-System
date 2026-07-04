import logging
import re
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from agents.base_agent import BaseAgent
from backend.mistral_client import MistralClient
from backend.chroma_manager import ChromaManager

logger = logging.getLogger(__name__)


class MarketAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Market Analysis Agent",
            "Market opportunity, competitors, pricing, and TAM analysis"
        )
        self.llm = MistralClient()
        self.chroma = ChromaManager(collection_name="vc_pitches_market")

        # HARD GUARANTEES / LIMITS
        self.SEARCH_QUERIES_PER_QUESTION = 3
        self.PAGES_PER_QUERY = 5
        self.MAX_CHARS_PER_PAGE = 5500      # slightly reduced → faster LLM calls

        # PARALLELISM CONTROLS — tune based on your infra & rate limits
        self.QUESTION_WORKERS = 6           # ← new: parallel questions
        self.SEARCH_WORKERS = 10
        self.FETCH_WORKERS = 30             # increased — network I/O bound

    # ==============================================================
    # 1. Generate Research Questions
    # ==============================================================
    def _generate_research_questions(self, pitch_data: Dict) -> List[str]:
        prompt = f"""
You are a VC market research strategist.

From the pitch below, generate 6–8 concrete market research questions
covering market size, competitors, pricing, adoption, growth, and risks.

Pitch:
{pitch_data}

Return ONLY bullet-point questions.
"""
        resp = self.llm.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )

        questions = [
            re.sub(r"^[\-•\d\.]+\s*", "", ln).strip()
            for ln in resp.splitlines()
            if ln.strip() and len(ln.strip()) > 15
        ]
        return questions[:8]

    # ==============================================================
    # 2. Rewrite Question → Search Queries
    # ==============================================================
    def _rewrite_search_queries(self, question: str) -> List[str]:
        prompt = f"""
Rewrite the question into {self.SEARCH_QUERIES_PER_QUESTION}
effective Google/Bing-style search queries likely to surface reports,
pricing pages, statistics, industry blogs or credible sources.

Question:
{question}

Return one query per line — nothing else.
"""
        resp = self.llm.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120,
        )

        queries = [q.strip() for q in resp.splitlines() if len(q.strip()) > 8]
        return queries[:self.SEARCH_QUERIES_PER_QUESTION]

    # ==============================================================
    # 3. Web Search (single query)
    # ==============================================================
    def _search_links(self, query: str) -> List[str]:
        try:
            url = "https://www.bing.com/search"
            params = {"q": query}
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

            html = requests.get(url, params=params, headers=headers, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            links = []

            for a in soup.select("li.b_algo h2 a"):
                href = a.get("href")
                if href and href.startswith(("http://", "https://")):
                    links.append(href)
                if len(links) >= self.PAGES_PER_QUERY:
                    break

            return links
        except Exception as e:
            logger.warning(f"Search failed for '{query}': {e}")
            return []

    # ==============================================================
    # 4. Fetch Page (single URL)
    # ==============================================================
    def _fetch_page_text(self, url: str) -> Dict[str, str]:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=12)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "iframe", "footer", "header"]):
                tag.decompose()

            text = " ".join(soup.get_text(separator=" ").split())
            return {"url": url, "text": text[:self.MAX_CHARS_PER_PAGE]}
        except Exception as e:
            logger.debug(f"Fetch failed for {url}: {e}")
            return {}

    # ==============================================================
    # 5. Extract Structured Signals
    # ==============================================================
    def _extract_market_signals(self, question: str, docs: List[Dict]) -> Dict:
        if not docs:
            return {}

        context = "\n\n".join(
            f"Source: {d['url']}\n{d['text']}" for d in docs
        )[:8500]  # slightly increased, still safe

        prompt = f"""
You are a market intelligence analyst.

Extract structured signals from ALL provided sources.

Question being answered:
{question}

Context (multiple sources):
{context}

Return **valid JSON only** with these keys (use empty arrays if no data):
{{
  "market_numbers": list[str],
  "growth_rates": list[str],
  "competitors": list[str],
  "pricing_models": list[str],
  "customer_segments": list[str],
  "notable_claims": list[str],
  "sources": list[str]
}}
"""
        resp = self.llm.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=700,
        )

        try:
            cleaned = resp.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
            import json
            return json.loads(cleaned)
        except Exception:
            logger.warning(f"JSON parse failed for question: {question}")
            return {"raw_output": resp, "parse_error": True}

    # ==============================================================
    # 6. Market Size Estimation
    # ==============================================================
    def _estimate_market(self, pitch_data: Dict, signals: List[Dict]) -> str:
        prompt = f"""
You are a VC analyst.

Using the startup pitch and ALL extracted market signals below,
estimate the **Total Addressable Market (TAM)** in USD.

Pitch:
{pitch_data}

Aggregated signals from multiple questions:
{signals}

Rules:
- Use proxy metrics when direct data missing
- State key assumptions explicitly
- Prefer a realistic range over single point estimate
- Be conservative — avoid hype
"""
        return self.llm.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=350,
        )

    # ==============================================================
    # 7. Store Findings
    # ==============================================================
    def _store_findings(self, question: str, signals: Dict, pitch_data: Dict):
        text = f"Question: {question}\nSignals: {signals}"
        metadata = {
            "type": "market_research",
            "question": question,
            "company_name": pitch_data.get("company_name", ""),
            "industry": pitch_data.get("industry", ""),
            "stage": pitch_data.get("stage", ""),
        }
        try:
            self.chroma.upsert_data([text], [metadata])
        except Exception as e:
            logger.error(f"Chroma upsert failed: {e}")

    # ==============================================================
    # 8. Process ONE question (runs in parallel)
    # ==============================================================
    def _process_single_question(self, question: str, pitch_data: Dict) -> Dict:
        search_queries = self._rewrite_search_queries(question)

        # ── PARALLEL SEARCH ───────────────────────────────────────
        all_urls = []
        with ThreadPoolExecutor(max_workers=self.SEARCH_WORKERS) as executor:
            futures = [executor.submit(self._search_links, q) for q in search_queries]
            for future in as_completed(futures):
                try:
                    all_urls.extend(future.result())
                except Exception:
                    pass

        # Simple deduplication + cap
        seen = set()
        unique_urls = []
        for url in all_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        all_urls = unique_urls[:self.PAGES_PER_QUERY * self.SEARCH_QUERIES_PER_QUESTION]

        # ── PARALLEL FETCH ────────────────────────────────────────
        docs = []
        with ThreadPoolExecutor(max_workers=self.FETCH_WORKERS) as executor:
            futures = [executor.submit(self._fetch_page_text, url) for url in all_urls]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result and result.get("text"):
                        docs.append(result)
                except Exception:
                    pass

        signals = self._extract_market_signals(question, docs)

        finding = {
            "question": question,
            "search_queries": search_queries,
            "pages_crawled": len(docs),
            "signals": signals,
        }

        self._store_findings(question, signals, pitch_data)

        return {"finding": finding, "signals": signals}

    # ==============================================================
    # 9. Main Orchestration — PARALLEL across questions
    # ==============================================================
    def analyze_market(self, pitch_data: Dict) -> Dict:
        logger.info("MarketAnalysisAgent: Starting market analysis")

        questions = self._generate_research_questions(pitch_data)
        if not questions:
            return {"error": "No research questions generated", "questions": []}

        all_findings = []
        all_signals = []

        with ThreadPoolExecutor(max_workers=self.QUESTION_WORKERS) as executor:
            future_to_q = {
                executor.submit(self._process_single_question, q, pitch_data): q
                for q in questions
            }

            for future in as_completed(future_to_q):
                q = future_to_q[future]
                try:
                    result = future.result()
                    all_findings.append(result["finding"])
                    all_signals.append(result["signals"])
                    logger.info(f"Completed question: {q}")
                except Exception as exc:
                    logger.error(f"Question '{q}' generated an exception: {exc}")

        market_estimate = self._estimate_market(pitch_data, all_signals)

        return {
            "questions": questions,
            "findings": sorted(all_findings, key=lambda x: x["question"]),
            "market_size_estimate": market_estimate,
            "crawl_policy": f"{self.PAGES_PER_QUERY} pages/query max, {self.SEARCH_QUERIES_PER_QUESTION} queries/question, parallel questions & fetches",
            "questions_processed": len(all_findings),
        }

    # ==============================================================
    def process(self, data: Dict) -> Dict:
        return self.analyze_market(data)