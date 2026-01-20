from agents.base_agent import BaseAgent
from typing import Dict, List, Optional
from backend.mistral_client import MistralClient
from backend.qdrant_manager import QdrantManager
import logging
import json

logger = logging.getLogger(__name__)

class MarcusAgent(BaseAgent):
    def __init__(self):
        super().__init__("Marcus Agent", "Senior strategic advisor and mentor")
        self.mistral_client = MistralClient()
        self.qdrant_manager = QdrantManager()
        self.persona = None

    def set_persona(self, persona: Optional[Dict]):
        """Set the investor persona for this evaluation."""
        self.persona = persona
        if persona:
            logger.info(f"Marcus Agent now embodying persona: {persona.get('name', 'Unknown')}")

    def _build_chain_of_thought_prompt(self, pitch_data: Dict, evaluation_results: Dict, context_docs: List[Dict]) -> List[Dict]:
        persona_context = ""
        if self.persona:
            persona_context = f"""
You are {self.persona.get('name', 'Marcus')}, a {self.persona.get('title', 'strategic advisor')}.

**Your Persona & Philosophy:**
- Core traits: {', '.join(self.persona.get('traits', []))}
- Communication style: {self.persona.get('style', 'Direct and analytical')}
- Investment focus: {self.persona.get('description', '')}

**CRITICAL: Strictly embody this persona throughout your feedback. Use their exact evaluation framework, communication patterns, and priorities. Be authentic to their perspective. Your tone, word choice, and priorities should reflect this person exactly.**
"""

        prompt_parts = [
            persona_context or "You are Marcus, a senior venture capitalist and mentor.",
            "Your role is to provide high-level strategic guidance and insightful feedback on a startup pitch.",
            "Synthesize the analysis from various specialized agents and provide a nuanced, advisory, and realistic judgment.",
            "Consider the long-term scalability, viability, and vision of the startup.",
            "Your feedback should be structured into the following sections: Strategic Strengths, Critical Weaknesses, Growth Opportunities, Strategic Recommendations, and Final Note.",
            "\n---\n\nOriginal Startup Pitch:\n" + json.dumps(pitch_data, indent=2),
            "\n---\n\nAnalysis from Specialized Agents:\n"
        ]

        for agent_name, result in evaluation_results.items():
            prompt_parts.append(f"\n{agent_name.replace('_', ' ').title()} Analysis:\n" + json.dumps(result, indent=2))
        
        if context_docs:
            prompt_parts.append("\n---\n\nRelevant Historical Context/Memory from Qdrant:\n")
            for doc in context_docs:
                payload = doc.get('payload', {})
                content = payload.get('content') or f"Page {payload.get('page_number', '?')}: [reference]"
                prompt_parts.append(f"- {content}")

        prompt_parts.append("\n---\n\nBased on the above, provide your strategic evaluation and feedback, structured as requested:")

        return [
            {"role": "system", "content": "You are an investor providing authentic strategic feedback. Stay strictly in character and embody the persona's specific perspective."},
            {"role": "user", "content": "\n".join(prompt_parts)}
        ]

    def provide_strategic_feedback(self, pitch_data: Dict, evaluation_results: Dict) -> Dict:
        logger.info(f"Marcus Agent: Providing strategic feedback{' as ' + self.persona.get('name') if self.persona else ''}...")

        # Step 1: Inject Startup Memory (Optional)
        context_docs = []
        try:
            query_for_qdrant = pitch_data.get("content", "")
            if not query_for_qdrant and evaluation_results:
                query_for_qdrant = " ".join([json.dumps(res) for res in evaluation_results.values()])

            if query_for_qdrant:
                context_docs = self.qdrant_manager.search(query_for_qdrant, limit=3)
                logger.info(f"Marcus Agent: Retrieved {len(context_docs)} context documents from Qdrant.")
        except Exception as e:
            logger.warning(f"Marcus Agent: Could not retrieve context from Qdrant: {e}")
            context_docs = []

        # Step 2: Build a Chain-of-Thought Prompt
        messages = self._build_chain_of_thought_prompt(pitch_data, evaluation_results, context_docs)

        # Step 3: Call LLM API
        try:
            llm_response = self.mistral_client.call_openrouter_api(messages)
            logger.info("Marcus Agent: Received response from LLM.")
        except Exception as e:
            logger.error(f"Marcus Agent: Error calling LLM API: {e}")
            llm_response = "Marcus Agent encountered an error and could not provide strategic feedback."

        return {"strategic_feedback": llm_response}

    def process(self, data: Dict) -> Dict:
        pitch_data = data.get("pitch_data", {})
        evaluation_results = data.get("evaluation_results", {})
        
        if not pitch_data or not evaluation_results:
            logger.error("Marcus Agent: Missing 'pitch_data' or 'evaluation_results' in input data.")
            return {"strategic_feedback": "Marcus Agent could not process due to missing input data."}

        return self.provide_strategic_feedback(pitch_data, evaluation_results)
