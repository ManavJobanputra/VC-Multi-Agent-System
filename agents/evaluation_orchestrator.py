from agents.base_agent import BaseAgent
from typing import Dict, List

class EvaluationOrchestrator(BaseAgent):
    def __init__(self):
        super().__init__("Evaluation Orchestrator", "Central coordinator and decision maker")

    def ingest_pitch(self, pitch_data: Dict) -> Dict:
        # Placeholder for pitch ingestion and processing logic
        print("Ingesting pitch data...")
        return {"processed_pitch": pitch_data}

    def coordinate_evaluation(self, processed_pitch: Dict, agents: Dict[str, BaseAgent], progress_callback=None):
        print("Coordinating multi-agent evaluation...")
        results = {}
        progress = []
        ordered_agents = [
            "financial_analysis_agent",
            "market_analysis_agent",
            "risk_assessment_agent",
            "team_assessment_agent",
            "execution_agent",
            "marcus_agent",
        ]
        for agent_name in ordered_agents:
            agent_instance = agents.get(agent_name)
            if not agent_instance:
                continue
            print(f"  - Running {agent_name}...")
            if progress_callback:
                progress_callback(agent_name, "in_progress")
            progress.append({"agent": agent_name, "status": "started"})
            if agent_name == "marcus_agent":
                results[agent_name] = agent_instance.process({
                    "pitch_data": processed_pitch["processed_pitch"],
                    "evaluation_results": results
                })
            else:
                results[agent_name] = agent_instance.process(processed_pitch["processed_pitch"])
            if progress_callback:
                progress_callback(agent_name, "completed")
            progress.append({"agent": agent_name, "status": "completed"})
        return results, progress

    def generate_overall_feedback(self, evaluation_results: Dict) -> Dict:
        print("Generating overall feedback...")
        overall_feedback = {"summary": "Comprehensive evaluation complete.", "details": evaluation_results}
        return overall_feedback

    def process(self, data: Dict) -> Dict:
        # The orchestrator's process method is not meant to be called directly for evaluation.
        # Its methods like ingest_pitch, coordinate_evaluation, and generate_overall_feedback
        # are called by the main application flow.
        return data # Or handle as appropriate, but not raise NotImplementedError

