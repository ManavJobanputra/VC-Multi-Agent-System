import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from tavily import TavilyClient

from agents.base_agent import BaseAgent
from backend.pinecone_manager import PineconeManager
from backend.config import TAVILY_API_KEY
from backend.mistral_client import MistralClient

logger = logging.getLogger(__name__)


class MarketAnalysisAgent(BaseAgent):
    def __init__(self, pinecone_manager: Optional[PineconeManager] = None):
        super().__init__(
            "Market Analysis Agent",
            "Market opportunity, competitors, pricing, and TAM analysis"
        )
        self.llm = MistralClient()
        self.pinecone = pinecone_manager or PineconeManager(collection_name="vc_pitches_market")
        # Falls back to Tavily's keyless mode (rate-limited, no signup) if no key is configured.
        self.tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else TavilyClient()

        self.QUESTION_WORKERS = 4
        self.MAX_RESULTS_PER_QUESTION = 5
        self.MAX_CONTENT_CHARS_PER_SOURCE = 1500

    # ==============================================================
    # 1. Generate Research Questions
    # ==============================================================
    def _generate_research_questions(self, pitch_data: Dict) -> List[str]:
        prompt = f"""
You are a VC market research strategist.

From the pitch below, generate 6-8 concrete market research questions
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
    # 2. Research a single question via Tavily
    # ==============================================================
    def _research_question(self, question: str) -> Dict:
        """One Tavily call replaces the old search-links + fetch-pages pipeline:
        Tavily returns an AI-synthesized answer plus the source snippets it
        was drawn from, in a single round trip, instead of us scraping Bing
        HTML and crawling pages ourselves (which was silently blocked -
        every result came back unparseable)."""
        try:
            response = self.tavily.search(
                query=question,
                search_depth="advanced",
                include_answer="advanced",
                max_results=self.MAX_RESULTS_PER_QUESTION,
            )
        except Exception as e:
            logger.warning(f"Tavily search failed for '{question}': {e}")
            return {"question": question, "ok": False, "error": str(e), "sources": []}

        results = response.get("results") or []
        sources = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": (r.get("content") or "")[: self.MAX_CONTENT_CHARS_PER_SOURCE],
                "score": r.get("score"),
            }
            for r in results
        ]

        return {
            "question": question,
            "ok": bool(sources or response.get("answer")),
            "tavily_answer": response.get("answer") or "",
            "sources": sources,
        }

    # ==============================================================
    # 3. Extract Structured Signals from Tavily's research
    # ==============================================================
    def _extract_market_signals(self, research: Dict) -> Dict:
        if not research["ok"]:
            return {"insufficient_data": True, "reason": research.get("error", "No search results found")}

        context_parts = []
        if research["tavily_answer"]:
            context_parts.append(f"AI-synthesized answer: {research['tavily_answer']}")
        for s in research["sources"]:
            context_parts.append(f"Source: {s['title']} ({s['url']})\n{s['content']}")
        context = "\n\n".join(context_parts)[:8500]

        prompt = f"""
You are a market intelligence analyst.

Extract structured signals ONLY from the provided context below. Do not
invent numbers, competitors, or claims that aren't in the context.

Question being answered:
{research['question']}

Context:
{context}

Return **valid JSON only** with these keys. Each list item MUST be a short
plain string (e.g. "$300M India TAM by 2026 (source X)"), never a nested
object. Use empty arrays if no data in the context:
{{
  "market_numbers": list[str],
  "growth_rates": list[str],
  "competitors": list[str],
  "pricing_models": list[str],
  "customer_segments": list[str],
  "notable_claims": list[str]
}}
"""
        resp = self.llm.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )

        try:
            cleaned = resp.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            signals = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"JSON parse failed for question: {research['question']}")
            return {"insufficient_data": True, "reason": "Could not parse extracted signals"}

        signals["sources"] = [s["url"] for s in research["sources"]]
        return signals

    # ==============================================================
    # 4. Market Size Estimation
    # ==============================================================
    def _estimate_market(self, pitch_data: Dict, signals: List[Dict]) -> str:
        usable_signals = [s for s in signals if not s.get("insufficient_data")]

        if not usable_signals:
            return (
                "Market research unavailable: web search returned no usable data for any "
                "research question. Do not treat the pitch's own market-size claims as "
                "validated - they are unverified until real research succeeds."
            )

        prompt = f"""
You are a VC analyst.

Using the startup pitch and ALL extracted market signals below,
estimate the **Total Addressable Market (TAM)** in USD.

Pitch:
{pitch_data}

Aggregated signals from multiple questions (only from real web research - do not
supplement with outside knowledge beyond what's here):
{usable_signals}

Rules:
- Use proxy metrics when direct data is missing, but say so explicitly
- State key assumptions explicitly
- Prefer a realistic range over a single point estimate
- Be conservative - avoid hype
- If the signals are too thin to estimate responsibly, say so instead of guessing
"""
        return self.llm.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=500,
        )

    # ==============================================================
    # 5. Store Findings
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
            self.pinecone.upsert_data([text], [metadata])
        except Exception as e:
            logger.error(f"Chroma upsert failed: {e}")

    # ==============================================================
    # 6. Process ONE question (runs in parallel)
    # ==============================================================
    def _process_single_question(self, question: str, pitch_data: Dict) -> Dict:
        research = self._research_question(question)
        signals = self._extract_market_signals(research)
        self._store_findings(question, signals, pitch_data)

        finding = {
            "question": question,
            "sources": [s["url"] for s in research["sources"]],
            "signals": signals,
        }
        return {"finding": finding, "signals": signals}

    # ==============================================================
    # 7. Main Orchestration — PARALLEL across questions
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
                    all_findings.append({"question": q, "sources": [], "signals": {"insufficient_data": True, "reason": str(exc)}})
                    all_signals.append({"insufficient_data": True, "reason": str(exc)})

        market_estimate = self._estimate_market(pitch_data, all_signals)
        failed_count = sum(1 for s in all_signals if s.get("insufficient_data"))

        return {
            "questions": questions,
            "findings": sorted(all_findings, key=lambda x: x["question"]),
            "market_size_estimate": market_estimate,
            "research_provider": "tavily",
            "questions_processed": len(all_findings),
            "questions_with_usable_data": len(all_findings) - failed_count,
        }

    # ==============================================================
    def process(self, data: Dict) -> Dict:
        return self.analyze_market(data)
