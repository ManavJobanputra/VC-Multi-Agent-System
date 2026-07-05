import json
import logging
import re
from typing import Any, Dict

from agents.base_agent import BaseAgent
from backend.mistral_client import MistralClient

logger = logging.getLogger(__name__)


class RiskAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Risk Assessment Agent",
            description="Risk identification, severity scoring, and mitigation strategist"
        )
        self.mistral_client = MistralClient()

    # ------------------------------------------------------------------
    # LLM Extraction: pull the signals risk severity actually depends on
    # out of free-text pitch content. Real pitches don't arrive with
    # "teamSize" or "revenueModel" form fields - those have to be read
    # out of the narrative, the same way a human analyst would.
    # ------------------------------------------------------------------
    def _extract_risk_signals_with_llm(self, pitch_text: str, industry: str, stage: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert VC risk analyst extracting risk-relevant facts from a startup pitch.

Extract ONLY what is explicitly stated or clearly implied in the pitch text below.
Use "N/A", null, or an empty list if something isn't mentioned - do not invent details.

Industry: {industry or "N/A"}
Stage: {stage or "N/A"}

Return ONLY valid JSON with this shape:
{{
  "team_size_mentioned": "number as string, or N/A if not stated",
  "key_person_dependency": true/false/null (does the pitch describe the business as dependent on one specific founder's skills/relationships, e.g. a solo technical founder or a single rainmaker?),
  "revenue_model_type": "one of: subscription, transactional, usage-based, enterprise-contract, marketplace-take-rate, unclear",
  "monetization_stage": "one of: pre-revenue, early-revenue, scaling, N/A",
  "regulatory_exposure": ["list of regulatory areas the pitch's business model touches, e.g. healthcare/HIPAA, fintech/PCI, data-privacy/GDPR - empty list if none apply"],
  "technical_dependency_risk": "string describing reliance on third-party APIs/models/infra the pitch itself flags as a risk or dependency, or N/A",
  "competitive_moat_mentioned": "string describing any stated differentiation/moat (proprietary data, patents, network effects), or N/A if the pitch doesn't claim one"
}}

Startup Pitch:
{pitch_text}
"""
        messages = [
            {"role": "system", "content": "You extract structured risk-relevant data from startup pitches. Never invent facts not present in the text."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.mistral_client.call_openrouter_api(messages, temperature=0.1, max_tokens=600)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Risk signal extraction failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # Deterministic scoring on top of the extracted facts (never on raw
    # form fields that may not exist - industry/stage are the only two
    # fields the real PitchData model actually has, everything else here
    # comes from the LLM extraction above).
    # ------------------------------------------------------------------
    def _score_risks(self, extracted: Dict[str, Any], industry: str, stage: str) -> Dict[str, Dict]:
        industry_l = (industry or "").lower()
        stage_l = (stage or "").lower()
        early_stage = stage_l in ["idea", "pre-seed", "seed"]

        risks = {}

        # ---------------- TECHNOLOGICAL RISK ----------------
        tech_dependency = extracted.get("technical_dependency_risk") or "N/A"
        has_flagged_dependency = tech_dependency not in ("N/A", None, "")
        tech_severity = "High" if ("ai" in industry_l and early_stage) or has_flagged_dependency else "Medium"

        risks["technological_risk"] = {
            "severity": tech_severity,
            "description": "Scalability, model accuracy, and infrastructure reliability risks.",
            "reason": (
                f"Pitch itself flags a technical dependency: {tech_dependency}."
                if has_flagged_dependency
                else "AI systems often face performance and cost challenges as usage grows."
                if "ai" in industry_l
                else "No specific technical dependency flagged in the pitch; standard scaling risk applies."
            ),
            "mitigation": [
                "Early load testing and cost benchmarking",
                "Model monitoring and fallback systems",
                "Cloud cost optimization strategies"
            ]
        }

        # ---------------- MARKET RISK ----------------
        moat = extracted.get("competitive_moat_mentioned") or "N/A"
        has_moat = moat not in ("N/A", None, "")
        market_severity = "Low" if has_moat else ("High" if early_stage else "Medium")

        risks["market_risk"] = {
            "severity": market_severity,
            "description": "Risk of slow adoption or strong incumbent competition.",
            "reason": (
                f"Pitch claims a moat: {moat}."
                if has_moat
                else "No differentiation or moat stated in the pitch - crowded markets make unclear positioning especially risky."
            ),
            "mitigation": [
                "Clear ICP definition",
                "Strong positioning and niche focus",
                "Early customer validation and pilots"
            ]
        }

        # ---------------- EXECUTION / TEAM RISK ----------------
        team_size_raw = extracted.get("team_size_mentioned")
        team_size = None
        if team_size_raw and str(team_size_raw).strip().upper() != "N/A":
            try:
                team_size = int(re.sub(r"[^\d]", "", str(team_size_raw)) or 0)
            except ValueError:
                team_size = None

        key_person_dependency = extracted.get("key_person_dependency") is True

        if key_person_dependency or (team_size is not None and team_size < 3):
            execution_severity = "High"
        elif team_size is None:
            execution_severity = "Medium"  # pitch didn't say - treat as unknown, not automatically low
        else:
            execution_severity = "Medium" if team_size < 5 else "Low"

        reason_parts = []
        if key_person_dependency:
            reason_parts.append("pitch describes reliance on a single key person")
        if team_size is not None:
            reason_parts.append(f"team size mentioned as {team_size}")
        else:
            reason_parts.append("team size not stated in the pitch")

        risks["execution_risk"] = {
            "severity": execution_severity,
            "description": "Risk of delayed execution due to limited team capacity or key-person dependency.",
            "reason": "; ".join(reason_parts).capitalize() + ".",
            "mitigation": [
                "Clear ownership per function",
                "Hiring roadmap post-funding",
                "Advisor or fractional expert support"
            ]
        }

        # ---------------- FINANCIAL RISK ----------------
        revenue_model = (extracted.get("revenue_model_type") or "unclear").lower()
        monetization_stage = (extracted.get("monetization_stage") or "N/A").lower()

        if revenue_model == "unclear":
            financial_severity = "High"
        elif monetization_stage == "pre-revenue":
            financial_severity = "High"
        elif revenue_model == "subscription":
            financial_severity = "Medium"
        else:
            financial_severity = "Medium"

        risks["financial_risk"] = {
            "severity": financial_severity,
            "description": "Cash runway and monetization uncertainty.",
            "reason": (
                "Pitch does not clearly describe a revenue model."
                if revenue_model == "unclear"
                else f"Revenue model is {revenue_model}, monetization stage: {monetization_stage}."
            ),
            "mitigation": [
                "Conservative burn planning",
                "Annual pre-paid plans",
                "Early enterprise or services revenue"
            ]
        }

        # ---------------- REGULATORY RISK ----------------
        regulatory_exposure = extracted.get("regulatory_exposure") or []
        if regulatory_exposure:
            regulatory_severity = "High"
        elif "ai" in industry_l:
            regulatory_severity = "Medium"
        else:
            regulatory_severity = "Low"

        risks["regulatory_risk"] = {
            "severity": regulatory_severity,
            "description": "Potential data privacy and compliance challenges.",
            "reason": (
                f"Business model touches regulated areas: {', '.join(regulatory_exposure)}."
                if regulatory_exposure
                else "AI products may be affected by evolving data regulations."
                if "ai" in industry_l
                else "No specific regulatory exposure identified from industry or pitch content."
            ),
            "mitigation": [
                "GDPR-compliant data handling",
                "Clear data usage policies",
                "Legal review before enterprise expansion"
            ]
        }

        return risks

    def _overall_risk(self, risks: Dict[str, Dict]) -> str:
        severity_map = {"Low": 1, "Medium": 2, "High": 3}
        avg_score = sum(severity_map[r["severity"]] for r in risks.values()) / len(risks)

        if avg_score >= 2.5:
            return "High"
        elif avg_score >= 1.8:
            return "Medium"
        return "Low"

    # ------------------------------------------------------------------
    # Main Analysis
    # ------------------------------------------------------------------
    def assess_risks(self, pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        pitch_text = pitch_data.get("content", "")
        industry = pitch_data.get("industry") or ""
        stage = pitch_data.get("stage") or ""

        if not pitch_text:
            return {"status": "error", "message": "No pitch content provided."}

        extracted = self._extract_risk_signals_with_llm(pitch_text, industry, stage)
        if not extracted:
            return {
                "status": "incomplete",
                "message": "Could not extract risk signals from pitch content.",
            }

        risks = self._score_risks(extracted, industry, stage)

        return {
            "extracted_signals": extracted,
            "overall_risk_profile": self._overall_risk(risks),
            "risk_breakdown": risks,
        }

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.assess_risks(data)
