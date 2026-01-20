from agents.base_agent import BaseAgent
from typing import Dict, Any
import logging
import json
import re
from backend.mistral_client import MistralClient

logger = logging.getLogger(__name__)


class FinancialAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Financial Analysis Agent",
            "Financial health, projections, and capital efficiency analyst"
        )
        self.mistral_client = MistralClient()

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------

    def _to_number(self, value):
        """Safely convert LLM outputs to numeric values."""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        value = str(value).lower().replace(",", "").strip()

        match = re.match(r"([\d\.]+)\s*(k|m)?", value)
        if not match:
            return None

        number = float(match.group(1))
        multiplier = match.group(2)

        if multiplier == "k":
            number *= 1_000
        elif multiplier == "m":
            number *= 1_000_000

        return number

    # ------------------------------------------------------------------
    # LLM Extraction
    # ------------------------------------------------------------------

    def _extract_financial_data_with_llm(self, pitch_text: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert startup financial analyst.

Extract the following financial information from the startup pitch below.
If a value is not explicitly stated, return "N/A".
Return ONLY valid JSON. No explanation.

Fields:
- revenue_model
- funding_ask
- burn_rate
- profitability_timeline
- current_revenue
- projected_revenue_year1
- projected_revenue_year3

Startup Pitch:
{pitch_text}
"""

        messages = [
            {"role": "system", "content": "You extract structured financial data from startup pitches."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.mistral_client.call_openrouter_api(
                messages,
                temperature=0.1
            )

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")

            return json.loads(json_match.group())

        except Exception as e:
            logger.error(f"Financial extraction failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # Main Analysis
    # ------------------------------------------------------------------

    def analyze_financials(self, pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("FinancialAnalysisAgent: Starting analysis")

        pitch_text = pitch_data.get("content", "")
        if not pitch_text:
            return {
                "status": "error",
                "message": "No pitch content provided."
            }

        raw = self._extract_financial_data_with_llm(pitch_text)

        # Normalize numeric fields
        funding_ask = self._to_number(raw.get("funding_ask"))
        burn_rate = self._to_number(raw.get("burn_rate"))
        current_revenue = self._to_number(raw.get("current_revenue"))
        rev_y1 = self._to_number(raw.get("projected_revenue_year1"))
        rev_y3 = self._to_number(raw.get("projected_revenue_year3"))

        required = {
            "revenue_model": raw.get("revenue_model"),
            "funding_ask": funding_ask,
            "burn_rate": burn_rate,
            "projected_revenue_year1": rev_y1,
            "projected_revenue_year3": rev_y3
        }

        missing_questions = [
            f"Please clarify your {k.replace('_', ' ')}."
            for k, v in required.items()
            if v in [None, "N/A"]
        ]

        if missing_questions:
            return {
                "status": "incomplete",
                "follow_up_questions": missing_questions,
                "extracted_data": raw
            }

        # ---------------- Financial Signals ----------------

        runway_months = round(funding_ask / burn_rate, 1) if burn_rate > 0 else None
        growth_multiple = round(rev_y3 / rev_y1, 1) if rev_y1 and rev_y3 else None

        # ---------------- Assessments ----------------

        revenue_model = str(raw.get("revenue_model", "")).lower()

        if "subscription" in revenue_model or "saas" in revenue_model:
            revenue_quality = "High (Recurring Revenue)"
        elif "transaction" in revenue_model:
            revenue_quality = "Medium (Volume-dependent)"
        else:
            revenue_quality = "Unclear"

        risks = []
        if runway_months and runway_months < 9:
            risks.append("Short runway increases financing risk.")
        if growth_multiple and growth_multiple < 3:
            risks.append("Conservative revenue growth projections.")
        if not risks:
            risks.append("No major financial red flags detected.")

        # ---------------- Health Score ----------------

        health = "Moderate"
        if runway_months and runway_months >= 18 and growth_multiple and growth_multiple >= 5:
            health = "Strong"
        elif runway_months and runway_months < 9:
            health = "Weak"

        # ---------------- Final Report ----------------

        return {
            "title": "Financial Analysis Report",
            "summary": {
                "financial_health": health,
                "runway_months": runway_months,
                "revenue_growth_multiple": growth_multiple
            },
            "sections": [
                {
                    "heading": "Extracted Financials",
                    "content": {
                        "revenue_model": raw.get("revenue_model"),
                        "funding_ask": funding_ask,
                        "burn_rate": burn_rate,
                        "current_revenue": current_revenue,
                        "year_1_revenue_projection": rev_y1,
                        "year_3_revenue_projection": rev_y3
                    }
                },
                {
                    "heading": "Revenue Quality",
                    "content": revenue_quality
                },
                {
                    "heading": "Runway & Growth",
                    "content": {
                        "estimated_runway_months": runway_months,
                        "growth_multiple_y1_to_y3": growth_multiple
                    }
                },
                {
                    "heading": "Key Financial Risks",
                    "content": risks
                }
            ],
            "raw_llm_output": raw
        }

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.analyze_financials(data)