from agents.base_agent import BaseAgent
from typing import Dict, List, Optional
from backend.mistral_client import MistralClient
from backend.chroma_manager import ChromaManager
import logging
import json

logger = logging.getLogger(__name__)

class AnswerValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Answer Validation Agent", "Validates founder answers against market data and agent analysis")
        self.mistral_client = MistralClient()
        self.chroma_manager = ChromaManager()

    def validate_answer(self, question: str, answer: str, session_id: str, pitch_context: Dict) -> Dict:
        """
        Validate founder's answer against:
        1. Market analysis data
        2. Agent findings stored in Chroma
        3. Industry benchmarks
        4. Pitch context
        
        Returns validation result with recommendation for next action.
        """
        logger.info(f"Validating answer for session {session_id}")
        
        # Step 1: Retrieve relevant market data and agent analyses from Chroma
        query = f"{question} {answer} {pitch_context.get('industry', '')} {pitch_context.get('company_name', '')}"
        rag_results = self.chroma_manager.search(query, limit=10, session_filter=session_id)
        
        # Organize retrieved context
        agent_findings = []
        market_data = []
        pitch_info = []
        
        for doc in rag_results:
            payload = doc.get('payload', {})
            doc_type = payload.get('type', 'unknown')
            content = payload.get('content', '')
            
            if doc_type == 'agent_analysis':
                agent_findings.append({
                    'agent': payload.get('agent', 'Unknown'),
                    'content': content[:500]
                })
            elif doc_type == 'pitch_context':
                pitch_info.append(content[:300])
            elif doc_type == 'pitch_document':
                market_data.append(content[:300])
        
        # Step 2: Build validation prompt
        validation_prompt = self._build_validation_prompt(
            question, answer, agent_findings, market_data, pitch_info, pitch_context
        )
        
        # Step 3: Call LLM for validation
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert investment analyst validating founder claims against market data and specialist analysis. "
                        "Your job is to determine if the founder's answer is: ACCURATE, VAGUE, OPTIMISTIC, or CONTRADICTORY. "
                        "Provide specific evidence and recommend next action."
                    )
                },
                {"role": "user", "content": validation_prompt}
            ]
            
            validation_response = self.mistral_client.call_openrouter_api(messages, temperature=0.3)
            logger.info(f"Validation complete for session {session_id}")
            
            return {
                "question": question,
                "answer": answer,
                "validation": validation_response,
                "agent_findings": agent_findings,
                "context_retrieved": len(rag_results),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error during answer validation: {e}")
            return {
                "question": question,
                "answer": answer,
                "validation": "Validation unavailable - proceeding with caution",
                "agent_findings": agent_findings,
                "context_retrieved": len(rag_results),
                "error": str(e)
            }
    
    def _build_validation_prompt(
        self, 
        question: str, 
        answer: str, 
        agent_findings: List[Dict],
        market_data: List[str],
        pitch_info: List[str],
        pitch_context: Dict
    ) -> str:
        """Build a comprehensive validation prompt."""
        
        prompt_parts = [
            f"INVESTOR QUESTION: {question}",
            f"\nFOUNDER'S ANSWER: {answer}",
            f"\nCOMPANY: {pitch_context.get('company_name', 'N/A')} | INDUSTRY: {pitch_context.get('industry', 'N/A')} | STAGE: {pitch_context.get('stage', 'N/A')}",
        ]
        
        if agent_findings:
            prompt_parts.append("\n\nSPECIALIST AGENT FINDINGS:")
            for finding in agent_findings[:3]:  # Top 3 most relevant
                prompt_parts.append(f"- {finding['agent']}: {finding['content']}")
        
        if pitch_info:
            prompt_parts.append("\n\nPITCH CONTEXT:")
            for info in pitch_info[:2]:
                prompt_parts.append(f"- {info}")
        
        if market_data:
            prompt_parts.append("\n\nMARKET/DOCUMENT DATA:")
            for data in market_data[:2]:
                prompt_parts.append(f"- {data}")
        
        prompt_parts.append("""

VALIDATE THE ANSWER:
1. ACCURACY: Does it align with specialist findings and market data?
2. SPECIFICITY: Is it vague or specific with metrics/numbers?
3. CONSISTENCY: Does it contradict pitch context or agent analysis?
4. REALISM: Is it overly optimistic or grounded?

PROVIDE YOUR ANALYSIS IN THIS FORMAT:

VALIDATION STATUS: [ACCURATE / VAGUE / OPTIMISTIC / CONTRADICTORY]

EVIDENCE:
- [Specific point about why this classification]
- [Reference to agent findings or market data]
- [Any contradictions or gaps]

RECOMMENDED NEXT ACTION:
- [FOLLOW_UP: Ask clarifying question about X] OR [NEW_QUESTION: Move to different topic - founder answered well]

SUGGESTED NEXT QUESTION:
[Write the exact question the investor should ask next]
""")
        
        return "\n".join(prompt_parts)
    
    def process(self, data: Dict) -> Dict:
        """Process validation request."""
        question = data.get("question", "")
        answer = data.get("answer", "")
        session_id = data.get("session_id", "")
        pitch_context = data.get("pitch_context", {})
        
        if not question or not answer:
            logger.error("Missing question or answer for validation")
            return {"validation": "Insufficient data for validation"}
        
        return self.validate_answer(question, answer, session_id, pitch_context)
