import json
import logging
import re
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from backend.mistral_client import MistralClient

logger = logging.getLogger(__name__)


class ProgressAgent(BaseAgent):
    """Reasons across a founder's full session history rather than any
    single memo - the questions here (did you improve, did you actually
    incorporate feedback, what keeps going wrong) only make sense with
    more than one data point."""

    MIN_SESSIONS = 2

    def __init__(self):
        super().__init__(
            "Progress Agent",
            "Cross-session analysis of improvement, feedback incorporation, and recurring weaknesses"
        )
        self.mistral_client = MistralClient()

    def generate_progress_report(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(sessions) < self.MIN_SESSIONS:
            return {
                "status": "insufficient_data",
                "sessions_analyzed": len(sessions),
                "message": f"Complete at least {self.MIN_SESSIONS} sessions to unlock a progress report - you have {len(sessions)}.",
            }

        prompt = self._build_prompt(sessions)
        report = self._generate_structured_report(prompt, len(sessions))
        return report

    def _build_prompt(self, sessions: List[Dict[str, Any]]) -> str:
        parts = [
            "You are a VC partner who has coached this founder through multiple pitch diligence "
            "sessions over time, in chronological order (Session 1 is the earliest). Your job is to "
            "assess their trajectory as a founder being diligenced - not to re-review any single "
            "pitch, but to compare sessions against each other.",
            f"\n{len(sessions)} sessions, oldest first:",
        ]

        for idx, s in enumerate(sessions, 1):
            analysis = s.get("analysis") or {}
            parts.append(f"\n--- SESSION {idx} ({s.get('created_at', 'N/A')}) ---")
            parts.append(f"Company: {s.get('company_name', 'N/A')} | Industry: {s.get('industry', 'N/A')} | Stage: {s.get('stage', 'N/A')}")
            parts.append(f"Investment Score: {s.get('investment_score', 'N/A')}/10")
            if analysis.get("overall_verdict"):
                parts.append(f"Verdict: {analysis['overall_verdict']}")
            if analysis.get("pros"):
                parts.append(f"Strengths: {'; '.join(analysis['pros'][:5])}")
            if analysis.get("cons"):
                parts.append(f"Concerns: {'; '.join(analysis['cons'][:5])}")
            if analysis.get("bad_parts"):
                parts.append(f"Weak spots in conversation: {'; '.join(analysis['bad_parts'][:5])}")
            if analysis.get("risk_assessment"):
                risk_summary = []
                for key, val in analysis["risk_assessment"].items():
                    severity = val.get("severity") if isinstance(val, dict) else val
                    risk_summary.append(f"{key}={severity}")
                parts.append(f"Risk severities: {', '.join(risk_summary)}")
            if analysis.get("contradictions"):
                for c in analysis["contradictions"]:
                    parts.append(f"Contradiction raised: {c.get('topic')} - resolved: {c.get('resolved')}")
            if analysis.get("answer_quality"):
                low_quality = [q for q in analysis["answer_quality"] if q.get("rating", 5) <= 2]
                if low_quality:
                    parts.append(f"Poorly answered questions: {'; '.join(q.get('question', '') for q in low_quality[:5])}")
            if analysis.get("recommendations"):
                parts.append(f"Recommendations given THIS session (check later sessions for whether these were acted on): {'; '.join(analysis['recommendations'])}")

        parts.append("""

GENERATE A CROSS-SESSION PROGRESS REPORT AS JSON. Rules:

- Compare sessions to each other explicitly. Never describe a single session in isolation -
  every point must reference at least two sessions (e.g. "in Session 2 you were vague about
  burn rate; in Session 4 you gave exact monthly figures").
- Check whether recommendations given in an earlier session were actually acted on in a later
  one. If a recommendation from Session N was never addressed in any session after N, say so
  plainly - don't be generous.
- A "consistent weakness" must appear in multiple sessions, not just be a concern from one.
  Cite exactly which sessions it appeared in.
- Be specific and direct, not encouraging for its own sake - if there's been no real
  improvement, say that.

RESPOND WITH ONLY VALID JSON - NO MARKDOWN, NO CODE BLOCKS:

{
    "trajectory_summary": "2-3 sentence direct assessment of whether this founder is improving, plateauing, or regressing across sessions, citing specific sessions",
    "score_trend": "Improving/Plateauing/Declining/Mixed",
    "improvements": [
        {
            "area": "e.g. Financial specificity",
            "evidence": "Concrete comparison naming the earlier session's weakness and the later session's improvement",
            "sessions_involved": [1, 3]
        }
    ],
    "feedback_incorporation": [
        {
            "recommendation": "The specific recommendation given, and in which session",
            "status": "Addressed/Partially Addressed/Ignored",
            "evidence": "What happened in the following session(s) that shows this"
        }
    ],
    "consistent_weaknesses": [
        {
            "weakness": "Specific recurring issue",
            "sessions_affected": [1, 2, 4],
            "frequency": "e.g. 3 of 4 sessions",
            "severity": "Low/Medium/High"
        }
    ],
    "consistent_strengths": [
        {
            "strength": "Specific thing that's reliably good across sessions",
            "sessions_affected": [1, 2, 3, 4]
        }
    ],
    "overall_assessment": "A direct closing paragraph: the single most important thing this founder needs to fix before their next real fundraising conversation, and what's genuinely gotten better."
}

CRITICAL RULES:
- Base everything on the session data above - never invent details.
- sessions_affected/sessions_involved use the 1-indexed session numbers shown above (Session 1, Session 2, ...).
- Minimum 2 items in improvements, feedback_incorporation, and consistent_weaknesses where the data supports it - if there's truly only one or zero, say so rather than padding with generic filler.
""")
        return "\n".join(parts)

    def _generate_structured_report(self, prompt: str, session_count: int) -> Dict[str, Any]:
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a direct, evidence-driven VC partner tracking a founder's progress across multiple diligence sessions. Respond ONLY with valid JSON. No markdown, no code blocks, no extra text."
                },
                {"role": "user", "content": prompt}
            ]

            response = self.mistral_client.call_openrouter_api(messages, temperature=0.2, max_tokens=3000)

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

            report = json.loads(cleaned)
            report["status"] = "ok"
            report["sessions_analyzed"] = session_count
            return report
        except Exception as e:
            logger.error(f"Progress report generation failed: {e}")
            return {
                "status": "error",
                "sessions_analyzed": session_count,
                "message": "Could not generate the progress report due to a processing error. Please try again.",
            }

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sessions = data.get("sessions", [])
        return self.generate_progress_report(sessions)
