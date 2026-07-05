from agents.base_agent import BaseAgent
from typing import Dict, List, Optional
from backend.mistral_client import MistralClient
from backend.pinecone_manager import PineconeManager
import logging
import json
import re

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    def __init__(self, pinecone_manager: Optional[PineconeManager] = None):
        super().__init__("Analysis Agent", "Generates comprehensive investment analysis from conversation and agent findings")
        self.mistral_client = MistralClient()
        self.pinecone_manager = pinecone_manager or PineconeManager()

    def generate_investment_analysis(
        self,
        session_id: str,
        pitch_context: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """
        Generate comprehensive investment analysis by:
        1. Retrieving all Q&A pairs with validations
        2. Retrieving all agent analysis findings
        3. Synthesizing into a memo that reasons over the diligence
           session rather than just summarizing it - connecting evidence,
           tracking contradictions raised and resolved, and quantifying
           confidence rather than asserting everything with certainty.
        """
        logger.info(f"Generating investment analysis for session {session_id}")

        qa_pairs = self._retrieve_qa_pairs(session_id, pitch_context)
        agent_findings = self._retrieve_agent_analyses(session_id, pitch_context)
        validations = self._retrieve_validations(session_id)

        analysis_prompt = self._build_analysis_prompt(
            pitch_context, qa_pairs, agent_findings, validations, conversation_history
        )

        return self._generate_structured_analysis(analysis_prompt)

    def _retrieve_qa_pairs(self, session_id: str, pitch_context: Dict) -> List[Dict]:
        """Retrieve all Q&A pairs for this session."""
        try:
            company_name = pitch_context.get('companyName') or pitch_context.get('company_name', '')
            query = f"Q&A pairs {company_name}"
            results = self.pinecone_manager.search(query, limit=30, session_filter=session_id)

            qa_pairs = []
            for doc in results:
                payload = doc.get('payload', {})
                if payload.get('type') == 'qa_pair' and payload.get('qa_data'):
                    qa_data = payload['qa_data']
                    if isinstance(qa_data, str):
                        try:
                            qa_data = json.loads(qa_data)
                        except (json.JSONDecodeError, TypeError):
                            continue
                    qa_pairs.append(qa_data)

            logger.info(f"Retrieved {len(qa_pairs)} Q&A pairs")
            return qa_pairs
        except Exception as e:
            logger.warning(f"Could not retrieve Q&A pairs: {e}")
            return []

    def _retrieve_agent_analyses(self, session_id: str, pitch_context: Dict) -> List[Dict]:
        """Retrieve all specialist agent analyses."""
        try:
            company_name = pitch_context.get('companyName') or pitch_context.get('company_name', '')
            query = f"agent analysis {company_name}"
            results = self.pinecone_manager.search(query, limit=20, session_filter=session_id)

            agent_findings = []
            for doc in results:
                payload = doc.get('payload', {})
                if payload.get('type') == 'agent_analysis':
                    agent_findings.append({
                        'agent': payload.get('agent', 'Unknown'),
                        'content': payload.get('content', '')
                    })

            logger.info(f"Retrieved {len(agent_findings)} agent analyses")
            return agent_findings
        except Exception as e:
            logger.warning(f"Could not retrieve agent analyses: {e}")
            return []

    def _retrieve_validations(self, session_id: str) -> List[Dict]:
        """Retrieve all answer validations."""
        try:
            query = "answer validation"
            results = self.pinecone_manager.search(query, limit=20, session_filter=session_id)

            validations = []
            for doc in results:
                payload = doc.get('payload', {})
                if payload.get('type') == 'answer_validation':
                    validations.append({
                        'question': payload.get('question', ''),
                        'answer': payload.get('answer', ''),
                        'validation': payload.get('validation_summary', ''),
                    })

            logger.info(f"Retrieved {len(validations)} validations")
            return validations
        except Exception as e:
            logger.warning(f"Could not retrieve validations: {e}")
            return []

    def _build_analysis_prompt(
        self,
        pitch_context: Dict,
        qa_pairs: List[Dict],
        agent_findings: List[Dict],
        validations: List[Dict],
        conversation_history: List[Dict]
    ) -> str:
        """Build the memo-synthesis prompt. The instructions below exist
        because a first pass at this agent produced a memo that read like
        a templated summary rather than an analyst's reasoning: generic
        phrases ("strong traction", "good PMF") instead of numbers,
        conclusions with no evidence chain, a real founder-answer
        contradiction-and-clarification that got dropped entirely, and
        risk severities that didn't visibly follow from anything -
        including "Low" financial risk with no burn/runway data at all,
        when missing data should widen uncertainty, not resolve it."""

        prompt_parts = [
            "You are a senior VC partner writing an investment committee memo. "
            "You are reasoning over a due-diligence conversation, not summarizing it - "
            "every claim must trace back to a specific number, quote, or finding below.",
            "\n1. PITCH CONTEXT:",
            f"Company: {pitch_context.get('companyName') or pitch_context.get('company_name', 'N/A')}",
            f"Industry: {pitch_context.get('industry', 'N/A')}",
            f"Stage: {pitch_context.get('currentStage') or pitch_context.get('stage', 'N/A')}",
            f"Problem: {pitch_context.get('problemStatement', 'N/A')}",
            f"Solution: {pitch_context.get('solution', 'N/A')}",
            f"Traction: {pitch_context.get('traction', 'N/A')}",
        ]

        if qa_pairs:
            prompt_parts.append(
                f"\n2. FULL Q&A TRANSCRIPT FROM DILIGENCE ({len(qa_pairs)} exchanges, in order - "
                "watch for a question raising a concern (e.g. numbers not reconciling) followed "
                "later by an answer that resolves it. That resolution is one of the most important "
                "things in the entire session and must appear in your memo if it happened):"
            )
            for idx, qa in enumerate(qa_pairs[:25], 1):
                prompt_parts.append(f"\nQ{idx}: {qa.get('question', 'N/A')}")
                prompt_parts.append(f"A{idx}: {qa.get('answer', 'N/A')}")
                if qa.get('validation'):
                    prompt_parts.append(f"Validation{idx}: {qa.get('validation', '')[:600]}")

        if agent_findings:
            prompt_parts.append("\n3. SPECIALIST AGENT FINDINGS (one score + one-line summary per agent, in your output, must trace to these):")
            for finding in agent_findings[:6]:
                prompt_parts.append(f"\n{finding['agent']}:")
                prompt_parts.append(finding['content'][:1200])

        if validations:
            prompt_parts.append("\n4. STANDALONE ANSWER VALIDATIONS (full text, look here for CONTRADICTORY/VAGUE/OPTIMISTIC status):")
            for val in validations[:10]:
                prompt_parts.append(f"- Q: {val['question']}\n  Validation: {val['validation'][:600]}")

        prompt_parts.append("""

GENERATE THE INVESTMENT MEMO AS JSON. Follow every rule below - these exist
because a prior version of this memo failed each of them:

- NO GENERIC PHRASES. Never write "strong traction", "good PMF", "large
  market" etc. on their own. Every strength, weakness, and risk must
  include the specific number, quote, or finding it's based on.
- CONNECT EVIDENCE TO CONCLUSIONS. Do not state a risk severity or a
  strength without a "reasoning" field that names the specific data point
  driving it. "Financial risk: Low" with no reasoning is not acceptable.
- MISSING DATA IS NOT LOW RISK. If a category's key facts were never
  provided (e.g. no burn rate for financial risk, no team background for
  team risk), the severity must reflect that uncertainty - lean toward
  Medium or High, and set a LOW confidence score - never mark something
  Low severity purely because nothing negative was found.
- SURFACE CONTRADICTIONS AND THEIR RESOLUTIONS. Scan the Q&A transcript
  and validations for any point flagged CONTRADICTORY, inconsistent, or
  questioned, then check whether a later answer resolved it. Report this
  explicitly - if it happened, it is one of the most important events in
  the memo, more important than restating any single Q&A pair.
  If no contradiction occurred, return an empty list, don't invent one.
- SCORE EACH SPECIALIST AGENT SEPARATELY. Investors want to see where the
  agents disagree, not one merged opinion.
- QUANTIFY CONFIDENCE. Every risk category and every agent score gets a
  confidence (0-100) reflecting how much real evidence backs it up, not
  just the severity/score itself.
- RATE EACH ANSWER'S QUALITY. For every Q&A pair, rate 1-5 whether the
  founder's answer was substantive, evasive, contradictory, or missing.
- END WITH A REAL INVESTMENT THESIS. One paragraph a partner could read
  aloud in an investment committee meeting - the core bet, and the single
  biggest thing that has to be true for it to work.

RESPOND WITH ONLY VALID JSON - NO MARKDOWN, NO CODE BLOCKS, NO ADDITIONAL TEXT:

{
    "investment_thesis": "One paragraph: what this company is, why the opportunity could work, and the single biggest unresolved condition for conviction.",
    "pros": ["Specific strength with the number/quote it's based on", "..."],
    "cons": ["Specific weakness or red flag with evidence", "..."],
    "good_parts": ["What the founder demonstrated well in conversation, with evidence", "..."],
    "bad_parts": ["Where the founder was vague, evasive, or unconvincing, with evidence", "..."],
    "contradictions": [
        {
            "topic": "e.g. LTV:CAC payback period",
            "concern_raised": "What was inconsistent and in which exchange (reference Q# if possible)",
            "resolution": "How the founder clarified it, and in which exchange - or 'Not resolved' if it wasn't",
            "resolved": true
        }
    ],
    "risk_assessment": {
        "technical_risk": {"severity": "Low/Medium/High", "reasoning": "Specific evidence this is based on", "confidence": 70},
        "market_risk": {"severity": "Low/Medium/High", "reasoning": "...", "confidence": 70},
        "team_risk": {"severity": "Low/Medium/High", "reasoning": "...", "confidence": 70},
        "financial_risk": {"severity": "Low/Medium/High", "reasoning": "...", "confidence": 70},
        "regulatory_risk": {"severity": "Low/Medium/High", "reasoning": "...", "confidence": 70}
    },
    "agent_assessment": {
        "market_analysis": {"score": 7, "confidence": 65, "summary": "One line grounded in the market agent's actual finding"},
        "financial_analysis": {"score": 7, "confidence": 65, "summary": "..."},
        "risk_assessment": {"score": 7, "confidence": 65, "summary": "..."},
        "team_assessment": {"score": 7, "confidence": 65, "summary": "..."},
        "execution": {"score": 7, "confidence": 65, "summary": "..."}
    },
    "answer_quality": [
        {"question": "Question text (shortened if long)", "rating": 4, "reason": "Why this rating - substantive/vague/evasive/contradictory/missing"}
    ],
    "recommendation": {
        "decision": "Pass/Watch/Follow/Lead",
        "reasons_to_invest": ["Specific reason with evidence", "..."],
        "reasons_not_to_invest": ["Specific reason with evidence", "..."],
        "open_questions": ["Specific unresolved question a partner would still ask", "..."],
        "confidence": 55
    },
    "recommendations": ["Specific actionable recommendation for the founder or the deal team", "..."],
    "overall_verdict": "One sentence summary of the decision and the core reason",
    "investment_score": 6
}

CRITICAL RULES:
- Base ALL points on the actual Q&A pairs, validations, and agent findings above - never invent data.
- Score 1-10 where: 1-3=Pass, 4-6=Watch, 7-8=Follow, 9-10=Lead. recommendation.decision must match this range.
- Minimum 3 items per list field (pros, cons, good_parts, bad_parts, recommendations, reasons_to_invest, reasons_not_to_invest, open_questions) where the underlying material supports it.
- answer_quality must cover every Q&A pair provided above, in the same order.
""")

        return "\n".join(prompt_parts)

    def _generate_structured_analysis(self, prompt: str) -> Dict:
        """Generate and parse structured analysis."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a senior VC partner writing an investment committee memo. Respond ONLY with valid JSON. No markdown, no code blocks, no extra text. Start with { and end with }."
                },
                {"role": "user", "content": prompt}
            ]

            response = self.mistral_client.call_openrouter_api(messages, temperature=0.2, max_tokens=4000)
            logger.info(f"Analysis response length: {len(response)}")

            cleaned = response.strip()

            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
                cleaned = cleaned.strip()

            if not cleaned.startswith('{'):
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end + 1]

            analysis = json.loads(cleaned)
            logger.info(f"Successfully parsed analysis with keys: {list(analysis.keys())}")

            defaults = self._get_fallback_analysis()
            for key, default_value in defaults.items():
                if key not in analysis or not analysis[key]:
                    analysis[key] = default_value

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return self._get_fallback_analysis()
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self) -> Dict:
        """Return minimal valid analysis structure - used both as the
        hard fallback on total failure and to backfill any field the LLM
        omitted from an otherwise-valid response."""
        return {
            "investment_thesis": "Preliminary analysis incomplete - insufficient diligence data to form a thesis.",
            "pros": ["Analysis completed", "Founder engaged with diligence questions", "Data collected for review"],
            "cons": ["Further evaluation recommended", "Automated analysis may be incomplete", "Manual review needed"],
            "good_parts": ["Engagement demonstrated"],
            "bad_parts": ["Additional data needed"],
            "contradictions": [],
            "risk_assessment": {
                "technical_risk": {"severity": "Medium", "reasoning": "Insufficient data to assess confidently.", "confidence": 20},
                "market_risk": {"severity": "Medium", "reasoning": "Insufficient data to assess confidently.", "confidence": 20},
                "team_risk": {"severity": "Medium", "reasoning": "Insufficient data to assess confidently.", "confidence": 20},
                "financial_risk": {"severity": "Medium", "reasoning": "Insufficient data to assess confidently.", "confidence": 20},
                "regulatory_risk": {"severity": "Medium", "reasoning": "Insufficient data to assess confidently.", "confidence": 20},
            },
            "agent_assessment": {},
            "answer_quality": [],
            "recommendation": {
                "decision": "Watch",
                "reasons_to_invest": ["Insufficient data for a confident recommendation"],
                "reasons_not_to_invest": ["Diligence data incomplete or analysis failed"],
                "open_questions": ["Re-run diligence session or review manually"],
                "confidence": 10,
            },
            "recommendations": ["Continue due diligence", "Schedule manual review with investment team", "Validate financial projections"],
            "overall_verdict": "Preliminary analysis complete - additional review recommended",
            "investment_score": 5,
        }

    def process(self, data: Dict) -> Dict:
        """Process analysis generation request."""
        session_id = data.get("session_id", "")
        pitch_context = data.get("pitch_context", {})
        conversation_history = data.get("conversation_history", [])

        return self.generate_investment_analysis(session_id, pitch_context, conversation_history)
