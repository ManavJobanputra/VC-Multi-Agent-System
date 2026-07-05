from agents.base_agent import BaseAgent
from typing import Dict, List, Optional
from backend.mistral_client import MistralClient
from backend.pinecone_manager import PineconeManager
import logging
import json

logger = logging.getLogger(__name__)

class MarcusAgent(BaseAgent):
    def __init__(self):
        super().__init__("Marcus Agent", "Senior strategic advisor and mentor")
        self.mistral_client = MistralClient()
        self.pinecone_manager = PineconeManager()
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

        # Extract and synthesize specialist insights
        specialist_insights = "\n**KEY INSIGHTS FROM SPECIALIST AGENTS:**\n"
        for agent_name, result in evaluation_results.items():
            if agent_name != "marcus_agent" and isinstance(result, dict) and result.get("strategic_feedback"):
                specialist_insights += f"\n{agent_name.replace('_', ' ').title()}:\n{result['strategic_feedback'][:500]}\n"
            elif agent_name != "marcus_agent" and isinstance(result, dict):
                specialist_insights += f"\n{agent_name.replace('_', ' ').title()}: {json.dumps(result, indent=2)[:300]}\n"

        prompt_parts = [
            persona_context or "You are Marcus, a senior venture capitalist and mentor with deep experience identifying winners and losers.",
            "\nYou have access to deep analysis from specialist agents. Use their insights but add YOUR unique perspective.",
            "Your role is to synthesize analysis from specialized agents and provide SHARP, CANDID strategic feedback.",
            "Do NOT just repackage what others said. Add YOUR unique insights, challenge assumptions, and call out what matters.",
            "Consider: What are the real risks here? Is the founder delusional about TAM? Can they actually execute? What's the unfair advantage (or lack thereof)?",
            specialist_insights,
            "\nYour feedback should be structured into these sections:\n"
            "  1. THE REAL OPPORTUNITY (What's actually compelling here?)\n"
            "  2. CRITICAL RED FLAGS (What keeps you up at night? Where do specialist agents disagree with the founder?)\n"
            "  3. FOUNDER ASSESSMENT (Can they execute? Do they listen?)\n"
            "  4. WHAT NEEDS TO HAPPEN (Specific milestones or changes to de-risk this)\n"
            "  5. INVESTMENT THESIS (Would you lead/follow/pass and why?)\n",
            
            "Make your feedback MEMORABLE. Be direct. Show expertise. Don't hedge. Reference specialist findings when they matter.\n"
            "\n---\n\nOriginal Startup Pitch:\n" + json.dumps(pitch_data, indent=2),
            "\n---\n\nAnalysis from Specialized Agents:\n"
        ]

        for agent_name, result in evaluation_results.items():
            prompt_parts.append(f"\n{agent_name.replace('_', ' ').title()} Analysis:\n" + json.dumps(result, indent=2))
        
        if context_docs:
            prompt_parts.append("\n---\n\nRelevant Historical Context/Memory from Chroma:\n")
            for doc in context_docs:
                payload = doc.get('payload', {})
                content = payload.get('content') or f"Page {payload.get('page_number', '?')}: [reference]"
                prompt_parts.append(f"- {content}")

        prompt_parts.append("\n---\n\nProvide your authentic, insightful strategic evaluation now. Be specific, candid, and memorable. Synthesize specialist findings with your unique perspective:")

        return [
            {"role": "system", "content": "You are a seasoned investor providing authentic strategic feedback. Think like a VC who has seen thousands of pitches. Be candid about what works and what doesn't. Synthesize specialist insights while adding your own expertise. Stay strictly in character with the persona provided."},
            {"role": "user", "content": "\n".join(prompt_parts)}
        ]

    def provide_strategic_feedback(self, pitch_data: Dict, evaluation_results: Dict) -> Dict:
        logger.info(f"Marcus Agent: Providing strategic feedback{' as ' + self.persona.get('name') if self.persona else ''}...")

        # Step 1: Inject Startup Memory (Optional)
        context_docs = []
        try:
            query_text = pitch_data.get("content", "")
            if not query_text and evaluation_results:
                query_text = " ".join([json.dumps(res) for res in evaluation_results.values()])

            if query_text:
                context_docs = self.pinecone_manager.search(query_text, limit=3)
                logger.info(f"Marcus Agent: Retrieved {len(context_docs)} context documents from Chroma.")
        except Exception as e:
            logger.warning(f"Marcus Agent: Could not retrieve context from Chroma: {e}")
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
