from agents.base_agent import BaseAgent
from typing import Dict, Any

class RiskAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Risk Assessment Agent",
            description="Risk identification, severity scoring, and mitigation strategist"
        )

    def assess_risks(self, pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        stage = pitch_data.get("currentStage", "").lower()
        team_size = int(pitch_data.get("teamSize", 0))
        industry = pitch_data.get("industry", "").lower()
        revenue_model = pitch_data.get("revenueModel", "").lower()

        risks = {}

        # ---------------- TECHNOLOGICAL RISK ----------------
        tech_severity = "High" if "ai" in industry and stage in ["idea", "pre-seed", "seed"] else "Medium"

        risks["technological_risk"] = {
            "severity": tech_severity,
            "description": "Scalability, model accuracy, and infrastructure reliability risks.",
            "reason": "AI systems often face performance and cost challenges as usage grows.",
            "mitigation": [
                "Early load testing and cost benchmarking",
                "Model monitoring and fallback systems",
                "Cloud cost optimization strategies"
            ]
        }

        # ---------------- MARKET RISK ----------------
        market_severity = "High" if "saas" in industry and stage == "seed" else "Medium"

        risks["market_risk"] = {
            "severity": market_severity,
            "description": "Risk of slow adoption or strong incumbent competition.",
            "reason": "Crowded SaaS markets make differentiation difficult.",
            "mitigation": [
                "Clear ICP definition",
                "Strong positioning and niche focus",
                "Early customer validation and pilots"
            ]
        }

        # ---------------- EXECUTION / TEAM RISK ----------------
        execution_severity = "High" if team_size < 5 else "Medium"

        risks["execution_risk"] = {
            "severity": execution_severity,
            "description": "Risk of delayed execution due to limited team capacity.",
            "reason": "Small teams face bandwidth constraints across product, sales, and ops.",
            "mitigation": [
                "Clear ownership per function",
                "Hiring roadmap post-funding",
                "Advisor or fractional expert support"
            ]
        }

        # ---------------- FINANCIAL RISK ----------------
        financial_severity = "Medium" if "subscription" in revenue_model else "High"

        risks["financial_risk"] = {
            "severity": financial_severity,
            "description": "Cash runway and monetization uncertainty.",
            "reason": "Recurring revenue takes time to stabilize.",
            "mitigation": [
                "Conservative burn planning",
                "Annual pre-paid plans",
                "Early enterprise or services revenue"
            ]
        }

        # ---------------- REGULATORY RISK ----------------
        regulatory_severity = "Medium" if "ai" in industry else "Low"

        risks["regulatory_risk"] = {
            "severity": regulatory_severity,
            "description": "Potential data privacy and compliance challenges.",
            "reason": "AI products may be affected by evolving data regulations.",
            "mitigation": [
                "GDPR-compliant data handling",
                "Clear data usage policies",
                "Legal review before enterprise expansion"
            ]
        }

        return {
            "overall_risk_profile": self._overall_risk(risks),
            "risk_breakdown": risks
        }

    def _overall_risk(self, risks: Dict[str, Dict]) -> str:
        severity_map = {"Low": 1, "Medium": 2, "High": 3}
        avg_score = sum(severity_map[r["severity"]] for r in risks.values()) / len(risks)

        if avg_score >= 2.5:
            return "High"
        elif avg_score >= 1.8:
            return "Medium"
        return "Low"

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.assess_risks(data)