from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.base_agent import BaseAgent
from typing import Dict, List

# These five are independent of each other - none reads another's output -
# so they run concurrently. marcus_agent is the only one that needs the
# others' results, so it always runs last, once they've all finished.
PARALLEL_AGENTS = [
    "financial_analysis_agent",
    "market_analysis_agent",
    "risk_assessment_agent",
    "team_assessment_agent",
    "execution_agent",
]


class EvaluationOrchestrator(BaseAgent):
    def __init__(self):
        super().__init__("Evaluation Orchestrator", "Central coordinator and decision maker")

    def ingest_pitch(self, pitch_data: Dict) -> Dict:
        # Placeholder for pitch ingestion and processing logic
        print("Ingesting pitch data...")
        return {"processed_pitch": pitch_data}

    def coordinate_evaluation(self, processed_pitch: Dict, agents: Dict[str, BaseAgent], progress_callback=None):
        print("Coordinating multi-agent evaluation...")
        pitch = processed_pitch["processed_pitch"]
        results = {}
        progress = []

        runnable = [name for name in PARALLEL_AGENTS if agents.get(name)]

        def run_agent(agent_name):
            print(f"  - Running {agent_name}...")
            if progress_callback:
                progress_callback(agent_name, "in_progress")
            return agents[agent_name].process(pitch)

        for agent_name in runnable:
            progress.append({"agent": agent_name, "status": "started"})

        with ThreadPoolExecutor(max_workers=max(len(runnable), 1)) as executor:
            future_to_name = {executor.submit(run_agent, name): name for name in runnable}
            for future in as_completed(future_to_name):
                agent_name = future_to_name[future]
                results[agent_name] = future.result()
                if progress_callback:
                    progress_callback(agent_name, "completed")
                progress.append({"agent": agent_name, "status": "completed"})

        marcus = agents.get("marcus_agent")
        if marcus:
            print("  - Running marcus_agent...")
            progress.append({"agent": "marcus_agent", "status": "started"})
            if progress_callback:
                progress_callback("marcus_agent", "in_progress")
            results["marcus_agent"] = marcus.process({
                "pitch_data": pitch,
                "evaluation_results": results,
            })
            if progress_callback:
                progress_callback("marcus_agent", "completed")
            progress.append({"agent": "marcus_agent", "status": "completed"})

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

