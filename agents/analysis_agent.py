from agents.base_agent import BaseAgent
from typing import Dict, List, Optional
from backend.mistral_client import MistralClient
from backend.qdrant_manager import QdrantManager
import logging
import json

logger = logging.getLogger(__name__)

class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("Analysis Agent", "Generates comprehensive investment analysis from conversation and agent findings")
        self.mistral_client = MistralClient()
        self.qdrant_manager = QdrantManager()

    def generate_investment_analysis(
        self, 
        session_id: str, 
        pitch_context: Dict, 
        conversation_history: List[Dict]
    ) -> Dict:
        """
        Generate comprehensive investment analysis by:
        1. Retrieving all Q&A pairs with validations
        2. Retrieving all agent analysis findings
        3. Synthesizing into structured investment report
        """
        logger.info(f"Generating investment analysis for session {session_id}")
        
        # Step 1: Retrieve Q&A pairs from Qdrant
        qa_pairs = self._retrieve_qa_pairs(session_id, pitch_context)
        
        # Step 2: Retrieve agent analyses
        agent_findings = self._retrieve_agent_analyses(session_id, pitch_context)
        
        # Step 3: Retrieve answer validations
        validations = self._retrieve_validations(session_id)
        
        # Step 4: Build comprehensive analysis prompt
        analysis_prompt = self._build_analysis_prompt(
            pitch_context, qa_pairs, agent_findings, validations, conversation_history
        )
        
        # Step 5: Generate structured analysis
        return self._generate_structured_analysis(analysis_prompt)
    
    def _retrieve_qa_pairs(self, session_id: str, pitch_context: Dict) -> List[Dict]:
        """Retrieve all Q&A pairs for this session."""
        try:
            company_name = pitch_context.get('companyName') or pitch_context.get('company_name', '')
            query = f"Q&A pairs {company_name}"
            results = self.qdrant_manager.search(query, limit=30, session_filter=session_id)
            
            qa_pairs = []
            for doc in results:
                payload = doc.get('payload', {})
                if payload.get('type') == 'qa_pair' and payload.get('qa_data'):
                    qa_pairs.append(payload['qa_data'])
            
            logger.info(f"Retrieved {len(qa_pairs)} Q&A pairs")
            return qa_pairs
        except Exception as e:
            logger.warning(f"Could not retrieve Q&A pairs: {e}")
            return []
    
    def _retrieve_agent_analyses(self, session_id: str, pitch_context: Dict) -> List[Dict]:
        """Retrieve all specialist agent analyses."""
        try:
            company_name = pitch_context.get('companyName') or pitch_context.get('company_name', '')
            query = f"agent analysis {company_name}"
            results = self.qdrant_manager.search(query, limit=20, session_filter=session_id)
            
            agent_findings = []
            for doc in results:
                payload = doc.get('payload', {})
                if payload.get('type') == 'agent_analysis':
                    agent_findings.append({
                        'agent': payload.get('agent', 'Unknown'),
                        'content': payload.get('content', '')
                    })
            
            logger.info(f"Retrieved {len(agent_findings)} agent analyses")
            return agent_findings
        except Exception as e:
            logger.warning(f"Could not retrieve agent analyses: {e}")
            return []
    
    def _retrieve_validations(self, session_id: str) -> List[Dict]:
        """Retrieve all answer validations."""
        try:
            query = "answer validation"
            results = self.qdrant_manager.search(query, limit=20, session_filter=session_id)
            
            validations = []
            for doc in results:
                payload = doc.get('payload', {})
                if payload.get('type') == 'answer_validation':
                    validations.append({
                        'question': payload.get('question', ''),
                        'answer': payload.get('answer', ''),
                        'validation': payload.get('validation_summary', '')
                    })
            
            logger.info(f"Retrieved {len(validations)} validations")
            return validations
        except Exception as e:
            logger.warning(f"Could not retrieve validations: {e}")
            return []
    
    def _build_analysis_prompt(
        self,
        pitch_context: Dict,
        qa_pairs: List[Dict],
        agent_findings: List[Dict],
        validations: List[Dict],
        conversation_history: List[Dict]
    ) -> str:
        """Build comprehensive analysis prompt."""
        
        prompt_parts = [
            "You are an expert venture capital investment analyst. Generate a comprehensive investment analysis based on:",
            "\n1. PITCH CONTEXT:",
            f"Company: {pitch_context.get('companyName') or pitch_context.get('company_name', 'N/A')}",
            f"Industry: {pitch_context.get('industry', 'N/A')}",
            f"Stage: {pitch_context.get('currentStage') or pitch_context.get('stage', 'N/A')}",
            f"Problem: {pitch_context.get('problemStatement', 'N/A')}",
            f"Solution: {pitch_context.get('solution', 'N/A')}",
            f"Traction: {pitch_context.get('traction', 'N/A')}",
        ]
        
        if qa_pairs:
            prompt_parts.append("\n2. STRUCTURED Q&A FROM INVESTOR CONVERSATION:")
            for idx, qa in enumerate(qa_pairs[:15], 1):  # Top 15 most relevant
                prompt_parts.append(f"\nQ{idx}: {qa.get('question', 'N/A')}")
                prompt_parts.append(f"A{idx}: {qa.get('answer', 'N/A')}")
                if qa.get('validation'):
                    prompt_parts.append(f"Validation: {qa.get('validation', '')[:200]}")
        
        if agent_findings:
            prompt_parts.append("\n3. SPECIALIST AGENT FINDINGS:")
            for finding in agent_findings[:5]:  # Top 5 most relevant
                prompt_parts.append(f"\n{finding['agent']}:")
                prompt_parts.append(finding['content'][:400])
        
        if validations:
            prompt_parts.append("\n4. ANSWER VALIDATION INSIGHTS:")
            for val in validations[:5]:
                prompt_parts.append(f"- {val['question']}: {val['validation'][:150]}")
        
        prompt_parts.append("""

GENERATE COMPREHENSIVE INVESTMENT ANALYSIS:

Analyze the founder's actual answers, validation results, and specialist findings to create a thorough assessment.

RESPOND WITH ONLY VALID JSON - NO MARKDOWN, NO CODE BLOCKS, NO ADDITIONAL TEXT:

{
    "pros": [
        "Specific strength based on founder's answers and data",
        "Another validated strength with evidence",
        "Third strength from agent findings"
    ],
    "cons": [
        "Specific weakness or red flag identified",
        "Concern raised in validations or agent analysis",
        "Third concern with evidence"
    ],
    "good_parts": [
        "What founder demonstrated well in conversation",
        "Strong point in their pitch or execution",
        "Positive aspect from Q&A"
    ],
    "bad_parts": [
        "Area where founder was vague or unconvincing",
        "Gap identified in validations",
        "Weakness in their approach"
    ],
    "risk_assessment": {
        "technical_risk": "Low/Medium/High: specific technical concerns from analysis",
        "market_risk": "Low/Medium/High: market validation concerns from Q&A",
        "team_risk": "Low/Medium/High: team capability assessment from conversation",
        "financial_risk": "Low/Medium/High: financial metrics concerns from answers",
        "regulatory_risk": "Low/Medium/High: regulatory or compliance risks identified"
    },
    "recommendations": [
        "Specific actionable recommendation based on findings",
        "Another recommendation addressing identified gaps",
        "Third recommendation for de-risking or growth"
    ],
    "overall_verdict": "One clear sentence with investment recommendation (Pass/Follow/Lead) with specific reasoning based on the analysis",
    "investment_score": 6
}

CRITICAL RULES:
- Base ALL points on actual Q&A pairs, validations, and agent findings
- Be SPECIFIC - reference actual data from conversation
- Score 1-10 where: 1-3=Pass, 4-6=Watch, 7-8=Follow, 9-10=Lead
- Make verdict actionable and evidence-based
- Minimum 3 items per list
""")
        
        return "\n".join(prompt_parts)
    
    def _generate_structured_analysis(self, prompt: str) -> Dict:
        """Generate and parse structured analysis."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert investment analyst. Respond ONLY with valid JSON. No markdown, no code blocks, no extra text. Start with { and end with }."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = self.mistral_client.call_openrouter_api(messages, temperature=0.2)
            logger.info(f"Analysis response length: {len(response)}")
            
            # Parse JSON
            import re
            cleaned = response.strip()
            
            # Remove markdown if present
            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
                cleaned = cleaned.strip()
            
            # Extract JSON boundaries
            if not cleaned.startswith('{'):
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]
            
            analysis = json.loads(cleaned)
            logger.info(f"Successfully parsed analysis with keys: {list(analysis.keys())}")
            
            # Validate and set defaults if needed
            defaults = {
                'pros': ['Analysis completed'],
                'cons': ['Further evaluation recommended'],
                'good_parts': ['Engagement demonstrated'],
                'bad_parts': ['Additional data needed'],
                'risk_assessment': {
                    'technical_risk': 'Medium: Requires validation',
                    'market_risk': 'Medium: Requires validation',
                    'team_risk': 'Medium: Requires validation',
                    'financial_risk': 'Medium: Requires validation',
                    'regulatory_risk': 'Medium: Requires validation'
                },
                'recommendations': ['Continue due diligence'],
                'overall_verdict': 'Preliminary analysis complete - additional review recommended',
                'investment_score': 5
            }
            
            for key, default_value in defaults.items():
                if key not in analysis or not analysis[key]:
                    analysis[key] = default_value
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return self._get_fallback_analysis()
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            return self._get_fallback_analysis()
    
    def _get_fallback_analysis(self) -> Dict:
        """Return minimal valid analysis structure."""
        return {
            "pros": ["Pitch evaluation initiated", "Conversation completed", "Data collected"],
            "cons": ["Analysis generation encountered technical issues", "Manual review recommended", "System refinement needed"],
            "good_parts": ["Founder participated in full conversation", "Provided responses to investor questions"],
            "bad_parts": ["Technical processing limitation", "Incomplete automated analysis"],
            "risk_assessment": {
                "technical_risk": "Medium: Standard technical due diligence required",
                "market_risk": "Medium: Market validation in progress",
                "team_risk": "Medium: Team assessment ongoing",
                "financial_risk": "Medium: Financial review pending",
                "regulatory_risk": "Medium: Compliance review needed"
            },
            "recommendations": ["Schedule manual review with investment team", "Complete technical due diligence", "Validate financial projections"],
            "overall_verdict": "Manual review recommended - automated analysis encountered processing limitations",
            "investment_score": 5
        }
    
    def process(self, data: Dict) -> Dict:
        """Process analysis generation request."""
        session_id = data.get("session_id", "")
        pitch_context = data.get("pitch_context", {})
        conversation_history = data.get("conversation_history", [])
        
        return self.generate_investment_analysis(session_id, pitch_context, conversation_history)
