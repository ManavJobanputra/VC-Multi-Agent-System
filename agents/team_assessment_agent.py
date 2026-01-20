from agents.base_agent import BaseAgent
from typing import Dict, Any

class TeamAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Team Assessment Agent",
            description="Founding team evaluation, execution capability, and hiring-gap analyst"
        )

    def assess_team(self, pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        team_size = int(pitch_data.get("teamSize", 0))
        stage = pitch_data.get("currentStage", "").lower()
        industry = pitch_data.get("industry", "").lower()

        report = {}

        # ---------------- FOUNDER EXPERIENCE ----------------
        founder_strength = "Strong" if team_size >= 2 else "Moderate"

        report["founder_experience"] = {
            "assessment": founder_strength,
            "summary": "Founders demonstrate relevant technical and domain understanding.",
            "investor_view": "Positive founder-market alignment increases execution confidence."
        }

        # ---------------- TEAM COMPLETENESS ----------------
        if team_size < 5:
            completeness = "Incomplete"
            gaps = ["Sales", "Marketing", "Customer Success"]
        elif team_size < 10:
            completeness = "Partially Complete"
            gaps = ["Growth", "Enterprise Sales"]
        else:
            completeness = "Well Balanced"
            gaps = []

        report["team_completeness"] = {
            "status": completeness,
            "identified_gaps": gaps,
            "risk_level": "High" if completeness == "Incomplete" else "Medium" if gaps else "Low"
        }

        # ---------------- LEADERSHIP & EXECUTION ----------------
        execution_strength = "High" if stage in ["seed", "series a"] else "Medium"

        report["leadership_and_execution"] = {
            "strength": execution_strength,
            "observation": "Leadership shows structured execution planning and milestone clarity.",
            "execution_risk": "Low" if execution_strength == "High" else "Medium"
        }

        # ---------------- SCALING READINESS ----------------
        scaling_ready = team_size >= 6 and stage in ["seed", "series a"]

        report["scaling_readiness"] = {
            "ready": scaling_ready,
            "concerns": None if scaling_ready else "Team may face bandwidth constraints during rapid growth.",
            "recommendation": "Define post-funding hiring roadmap for next 6–12 months."
        }

        # ---------------- TEAM RISK SUMMARY ----------------
        report["team_risk_summary"] = {
            "overall_risk": self._overall_team_risk(report),
            "key_investor_concerns": gaps[:2] if gaps else [],
            "mitigation_plan": [
                "Strategic hires post-funding",
                "Advisor or fractional leadership roles",
                "Clear ownership across product, tech, and go-to-market"
            ]
        }

        return report

    def _overall_team_risk(self, report: Dict[str, Any]) -> str:
        if report["team_completeness"]["risk_level"] == "High":
            return "High"
        if report["team_completeness"]["risk_level"] == "Medium":
            return "Medium"
        return "Low"

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.assess_team(data)