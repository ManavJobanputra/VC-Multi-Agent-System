import json
import logging
import re
from typing import Any, Dict

from agents.base_agent import BaseAgent
from backend.mistral_client import MistralClient

logger = logging.getLogger(__name__)

# Research-backed signals this agent scores against:
#
# - Standard VC due diligence treats execution risk as "will this team
#   actually deliver the stated plan" - scrutinizing operational readiness,
#   workflow/scaling capacity, and whether the timeline for stated
#   milestones is realistic given team size and resources.
# - Milestones are stage-dependent: pre-seed/seed diligence looks for
#   validation milestones (MVP, initial customers, beta results); Series A+
#   looks for scaling milestones (revenue targets, market expansion,
#   product-market fit). A pitch's milestones should match its stage.
# - "Burn multiple" (net cash burn / net-new-ARR in the same period) is the
#   standard capital-efficiency metric VCs use to judge execution quality
#   quantitatively: ~2-3x is normal at pre-seed/seed, tightening to ~1-1.5x
#   by Series A, under 1x by Series C; above ~2.5x is considered inefficient
#   execution relative to capital spent.
# - Some VCs structure funding in milestone-based tranches specifically
#   because "can this team hit what they say they'll hit with this amount
#   of capital" is a distinct, checkable question from "is the market big."


class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__("Execution Agent", "Milestone feasibility and capital-efficiency analyst")
        self.mistral_client = MistralClient()

    # ------------------------------------------------------------------
    # LLM Extraction: pull the stated plan out of the pitch narrative -
    # milestones, timeline, what the raise will fund, and any burn/revenue
    # figures relevant to capital efficiency.
    # ------------------------------------------------------------------
    def _extract_execution_data_with_llm(self, pitch_text: str, stage: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert VC analyst extracting execution-plan facts from a startup pitch.

Extract ONLY what is explicitly stated or clearly implied. Use "N/A" or an
empty list if something isn't mentioned - do not invent numbers or plans.

Company stage: {stage or "N/A"}

Return ONLY valid JSON with this shape:
{{
  "stated_milestones": ["list of concrete goals/milestones mentioned, e.g. 'expand to 150 clinics'"],
  "stated_timeline": "string describing the timeframe for those milestones, or N/A",
  "funding_use": ["list of what the raise will be spent on, e.g. 'hire sales team', 'regulatory filing'"],
  "current_team_size_for_execution": "number as string or N/A - people actually available to execute the plan",
  "monthly_burn_rate": "number as string (USD/month) or N/A",
  "current_mrr": "number as string (USD) or N/A",
  "stated_growth_rate": "string (e.g. '18% MoM') or N/A"
}}

Startup Pitch:
{pitch_text}
"""
        messages = [
            {"role": "system", "content": "You extract structured execution-plan data from startup pitches. Never invent facts not present in the text."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.mistral_client.call_openrouter_api(messages, temperature=0.1, max_tokens=700)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Execution data extraction failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # Utils (same numeric-parsing convention as financial_analysis_agent)
    # ------------------------------------------------------------------
    def _to_number(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        value = str(value).lower().replace(",", "").replace("$", "").strip()
        match = re.match(r"([\d.]+)\s*(k|m)?", value)
        if not match:
            return None
        number = float(match.group(1))
        multiplier = match.group(2)
        if multiplier == "k":
            number *= 1_000
        elif multiplier == "m":
            number *= 1_000_000
        return number

    def _parse_mom_growth_pct(self, growth_str: str):
        if not growth_str or growth_str == "N/A":
            return None
        match = re.search(r"([\d.]+)\s*%", growth_str)
        return float(match.group(1)) / 100 if match else None

    # ------------------------------------------------------------------
    # Deterministic Burn Multiple calculation, benchmarked against
    # stage-specific norms (2-3x pre-seed/seed, 1-1.5x Series A, <1x
    # Series C+, >2.5x flagged as inefficient regardless of stage).
    # ------------------------------------------------------------------
    def _assess_capital_efficiency(self, extracted: Dict[str, Any], stage: str) -> Dict[str, Any]:
        monthly_burn = self._to_number(extracted.get("monthly_burn_rate"))
        current_mrr = self._to_number(extracted.get("current_mrr"))
        mom_growth = self._parse_mom_growth_pct(extracted.get("stated_growth_rate"))

        if monthly_burn is None or current_mrr is None or mom_growth is None:
            return {
                "insufficient_data": True,
                "reason": "Pitch doesn't state enough of burn rate / current MRR / growth rate to compute burn multiple.",
            }

        # Net-new-ARR approximated from this month's MRR growth, annualized -
        # this represents the ARR-equivalent impact of ONE month's growth,
        # so it must be compared against ONE month's burn (not annual burn,
        # which would compare 12 months of spend against 1 month of growth).
        net_new_arr = current_mrr * mom_growth * 12
        if net_new_arr <= 0:
            return {"insufficient_data": True, "reason": "Growth rate implies no net-new revenue to compare burn against."}

        burn_multiple = round(monthly_burn / net_new_arr, 2)

        stage_lower = (stage or "").lower()
        if "series c" in stage_lower or "series d" in stage_lower:
            benchmark, threshold = "under 1x", 1.0
        elif "series a" in stage_lower or "series b" in stage_lower:
            benchmark, threshold = "1-1.5x", 1.5
        else:
            benchmark, threshold = "2-3x", 3.0

        efficient = burn_multiple <= threshold
        return {
            "insufficient_data": False,
            "burn_multiple": burn_multiple,
            "stage_benchmark": benchmark,
            "assessment": (
                f"Burn multiple of {burn_multiple}x is within the {benchmark} norm for {stage or 'this'} stage."
                if efficient
                else f"Burn multiple of {burn_multiple}x exceeds the {benchmark} norm for {stage or 'this'} stage - "
                     "capital efficiency is a concern regardless of how large the market opportunity is."
            ),
        }

    # ------------------------------------------------------------------
    # LLM Judgment: is the stated timeline realistic for the stated
    # milestones given the team and funding described? This is inherently
    # a judgment call, not a lookup table.
    # ------------------------------------------------------------------
    def _assess_milestone_feasibility(self, pitch_text: str, extracted: Dict[str, Any]) -> str:
        prompt = f"""
You are a sharp VC partner assessing execution feasibility: given this team's
described size and resources, is the stated timeline realistic for the
stated milestones, or is it founder optimism disconnected from what the
team can actually deliver?

Extracted execution plan:
{json.dumps(extracted, indent=2)}

Full pitch for context:
{pitch_text}

In 2-4 sentences, give a direct, candid feasibility assessment. Call out
specifically if the scope-to-timeline-to-team ratio looks unrealistic
(e.g. 10x expansion in under a year with no described hires to support it).
If the pitch states no concrete milestones or timeline, say so plainly
instead of assuming the plan is fine.
"""
        return self.mistral_client.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )

    # ------------------------------------------------------------------
    # Main Analysis
    # ------------------------------------------------------------------
    def execute_recommendation(self, pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("ExecutionAgent: Starting analysis")

        pitch_text = pitch_data.get("content", "")
        stage = pitch_data.get("stage", "")

        if not pitch_text:
            return {"status": "error", "message": "No pitch content provided."}

        extracted = self._extract_execution_data_with_llm(pitch_text, stage)
        if not extracted:
            return {"status": "incomplete", "message": "Could not extract execution plan from pitch content."}

        capital_efficiency = self._assess_capital_efficiency(extracted, stage)
        feasibility = self._assess_milestone_feasibility(pitch_text, extracted)

        risks = []
        if not extracted.get("stated_milestones"):
            risks.append("Pitch does not state concrete, checkable milestones.")
        if extracted.get("stated_timeline") in (None, "N/A"):
            risks.append("No timeline given for stated goals - can't assess pacing.")
        if capital_efficiency.get("insufficient_data") is False and "exceeds" in capital_efficiency.get("assessment", ""):
            risks.append("Burn multiple exceeds stage-appropriate benchmark.")
        if extracted.get("stated_milestones") and extracted.get("current_team_size_for_execution") in (None, "N/A"):
            risks.append("Pitch has concrete growth milestones but doesn't say what team size will execute them.")

        overall_risk = "High" if len(risks) >= 2 else ("Medium" if risks else "Low")

        return {
            "title": "Execution Feasibility Report",
            "extracted_execution_plan": extracted,
            "capital_efficiency": capital_efficiency,
            "milestone_feasibility_assessment": feasibility,
            "execution_risk_summary": {
                "overall_risk": overall_risk,
                "key_risks": risks or ["No major execution red flags identified from available information."],
            },
        }

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute_recommendation(data)
