import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Load configuration from .env
from config import HOST, PORT, DEBUG

from mistral_client import MistralClient
from qdrant_manager import QdrantManager
from rag_system import RAGSystem
from deck_processor import process_pitch_file, build_page_documents
from agents.evaluation_orchestrator import EvaluationOrchestrator
from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.team_assessment_agent import TeamAssessmentAgent
from agents.marcus_agent import MarcusAgent
from agents.execution_agent import ExecutionAgent
from voice_processing import VoiceProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]] = []
    pitch_context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class VoiceChatRequest(BaseModel):
    audio: str
    history: List[Dict[str, Any]] = []
    pitch_context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class AnalysisRequest(BaseModel):
    pitch_context: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, Any]] = []


class PitchData(BaseModel):
    content: str
    company_name: Optional[str] = None
    founder_name: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None
    pitch_file_name: Optional[str] = None
    pitch_file_base64: Optional[str] = None


class EvaluatePitchRequest(BaseModel):
    pitch_data: PitchData
    persona: Optional[Dict[str, Any]] = None


app = FastAPI(title="VC Multi-Agent System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
mistral_client = MistralClient()
qdrant_manager = QdrantManager()
rag_system = RAGSystem(qdrant_manager, mistral_client)
voice_processor = VoiceProcessor()

# Initialize agents
agents = {
    "evaluation_orchestrator": EvaluationOrchestrator(),
    "financial_analysis_agent": FinancialAnalysisAgent(),
    "market_analysis_agent": MarketAnalysisAgent(),
    "risk_assessment_agent": RiskAssessmentAgent(),
    "team_assessment_agent": TeamAssessmentAgent(),
    "marcus_agent": MarcusAgent(),
    "execution_agent": ExecutionAgent()
}

# Global state for progress tracking
_evaluation_progress = {}
_conversation_history = {}  # Store conversation per session
_evaluation_results = {}  # Store evaluation results for analysis


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message:
        raise HTTPException(status_code=400, detail="No message provided")
    
    # Get or create session ID
    session_id = req.session_id or str(uuid4())
    
    # Build context from pitch and history
    context_prompt = ""
    if req.pitch_context:
        context_prompt = f"Context: Company {req.pitch_context.get('company_name')}, {req.pitch_context.get('industry')}, Stage: {req.pitch_context.get('stage')}\n"
    
    # Prepare RAG context from conversation history - FILTER BY SESSION
    rag_query = req.message
    rag_results = qdrant_manager.search(rag_query, limit=3, session_filter=session_id)
    rag_context = "\n".join([doc.get('payload', {}).get('content', '') for doc in rag_results]) if rag_results else ""
    
    # Call LLM with context
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful investor advisor. Ask only one clarifying question at a time, "
                "wait for the user's reply before the next question, and keep answers concise. "
                f"{context_prompt}"
            ),
        },
    ]
    
    # Add conversation history
    for msg in req.history[-5:]:  # Last 5 for context window
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    
    # Add current message with RAG context
    if rag_context:
        messages.append({"role": "user", "content": f"{req.message}\n\n[Context: {rag_context}]"})
    else:
        messages.append({"role": "user", "content": req.message})
    
    response_text = mistral_client.call_openrouter_api(messages)
    
    # Check if agent thinks they have enough info to end conversation
    history_summary = "\n".join([f"{msg.get('role')}: {msg.get('content')[:100]}..." for msg in req.history[-3:]])
    end_check_messages = [
        {
            "role": "system",
            "content": "Analyze the conversation so far. Do you have enough information to make a comprehensive investment decision? Reply with ONLY 'END_CONVERSATION' if yes, or 'CONTINUE' if more info is needed."
        },
        {"role": "user", "content": f"Conversation summary:\n{history_summary}"}
    ]
    
    end_decision = mistral_client.call_openrouter_api(end_check_messages).strip().upper()
    conversation_ended = "END_CONVERSATION" in end_decision
    
    # Store in Qdrant for RAG retrieval with SESSION ID
    try:
        qdrant_manager.upsert_data(
            [req.message, response_text],
            [
                {"type": "user_message", "conversation": True, "session_id": session_id, "content": req.message},
                {"type": "assistant_response", "conversation": True, "session_id": session_id, "content": response_text}
            ]
        )
    except Exception as e:
        logger.warning(f"Could not store conversation to Qdrant: {e}")
    
    return {
        "response": response_text,
        "conversation_ended": conversation_ended,
        "end_reason": "Agent has gathered sufficient information for analysis" if conversation_ended else None,
        "session_id": session_id
    }


@app.post("/voice_chat")
def voice_chat(req: VoiceChatRequest):
    if not req.audio:
        raise HTTPException(status_code=400, detail="No audio provided")

    # Get or create session ID
    session_id = req.session_id or str(uuid4())

    # Transcribe audio
    transcribed_text = voice_processor.transcribe_audio(req.audio)
    logger.info(f"Transcribed text: {transcribed_text}")

    if "Could not understand audio" in transcribed_text or "Speech recognition service error" in transcribed_text:
        response_audio = voice_processor.generate_audio("I could not understand your audio. Please try again.")
        return {"response_audio": response_audio, "response_text": "I could not understand your audio. Please try again."}

    # Build context from pitch and history
    context_prompt = ""
    if req.pitch_context:
        context_prompt = f"Context: Company {req.pitch_context.get('company_name')}, {req.pitch_context.get('industry')}, Stage: {req.pitch_context.get('stage')}\n"
    
    # Prepare RAG context - FILTER BY SESSION
    rag_results = qdrant_manager.search(transcribed_text, limit=3, session_filter=session_id)
    rag_context = "\n".join([doc.get('payload', {}).get('content', '') for doc in rag_results]) if rag_results else ""
    
    # Call LLM with context
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful investor advisor. Ask only one clarifying question at a time, "
                "wait for the user's reply before the next, and keep responses concise for voice. "
                f"{context_prompt}"
            ),
        },
    ]
    
    # Add conversation history
    for msg in req.history[-5:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    
    # Add current message
    if rag_context:
        messages.append({"role": "user", "content": f"{transcribed_text}\n\n[Context: {rag_context}]"})
    else:
        messages.append({"role": "user", "content": transcribed_text})
    
    response_text = mistral_client.call_openrouter_api(messages)
    logger.info(f"LLM Response: {response_text}")

    # Generate response audio
    response_audio_base64 = voice_processor.generate_audio(response_text)
    
    # Store in Qdrant for RAG retrieval with SESSION ID
    try:
        qdrant_manager.upsert_data(
            [transcribed_text, response_text],
            [
                {"type": "user_voice_message", "conversation": True, "session_id": session_id, "content": transcribed_text},
                {"type": "assistant_voice_response", "conversation": True, "session_id": session_id, "content": response_text}
            ]
        )
    except Exception as e:
        logger.warning(f"Could not store voice conversation to Qdrant: {e}")
    
    return {"response_audio": response_audio_base64, "response_text": response_text, "session_id": session_id}


@app.post("/evaluate_pitch")
def evaluate_pitch(req: EvaluatePitchRequest):
    global _evaluation_progress
    _evaluation_progress = {}
    
    # Generate unique session ID for this pitch
    session_id = str(uuid4())
    
    pitch_data = req.pitch_data.dict()

    if not pitch_data.get("content"):
        raise HTTPException(status_code=400, detail="No pitch content provided. Please include a 'content' field in your pitch_data.")

    pitch_file_name = pitch_data.get("pitch_file_name")
    pitch_file_base64 = pitch_data.get("pitch_file_base64")
    pages = process_pitch_file(pitch_file_name, pitch_file_base64, mistral_client.call_vision_api)

    if pages:
        metadata_base = {
            "company_name": pitch_data.get("company_name"),
            "founder_name": pitch_data.get("founder_name"),
            "email": pitch_data.get("email"),
            "pitch_file_name": pitch_file_name,
            "session_id": session_id,
            "type": "pitch_document"
        }
        docs = build_page_documents(pages, metadata_base)
        if docs:
            # Add session_id to each doc's metadata
            for doc in docs:
                doc["metadata"]["session_id"] = session_id
            qdrant_manager.upsert_data(
                [d["text"] for d in docs],
                [d["metadata"] for d in docs]
            )

    orchestrator = agents["evaluation_orchestrator"]
    processed_pitch = orchestrator.ingest_pitch(pitch_data)
    evaluation_results, progress = orchestrator.coordinate_evaluation(processed_pitch, agents, progress_callback=lambda agent_name, status: _update_progress(agent_name, status))
    
    # Pass persona to Marcus agent
    marcus_agent = agents["marcus_agent"]
    marcus_agent.set_persona(req.persona)
    
    final_feedback = orchestrator.generate_overall_feedback(evaluation_results)

    return {
        "feedback": final_feedback,
        "agent_progress": progress,
        "deck_pages": pages,
        "session_id": session_id
    }


@app.get("/progress")
def get_progress():
    """Return current evaluation progress for real-time frontend updates."""
    return _evaluation_progress


@app.post("/generate_analysis")
def generate_analysis(req: AnalysisRequest):
    """Generate comprehensive investment analysis from conversation and pitch."""
    try:
        if not req.pitch_context or not req.conversation_history:
            raise HTTPException(status_code=400, detail="Pitch context and conversation history required")
        
        pitch_summary = f"""
Company: {req.pitch_context.get('companyName', req.pitch_context.get('company_name', 'N/A'))}
Industry: {req.pitch_context.get('industry', 'N/A')}
Stage: {req.pitch_context.get('currentStage', req.pitch_context.get('stage', 'N/A'))}
Problem: {req.pitch_context.get('problemStatement', 'N/A')}
Solution: {req.pitch_context.get('solution', 'N/A')}
Traction: {req.pitch_context.get('traction', 'N/A')}
"""

        conversation_summary = "\n".join([
            f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}" 
            for msg in req.conversation_history[-10:]  # Last 10 messages
        ])

        analysis_prompt = f"""
You are an expert investor. Based on the pitch and conversation, provide a comprehensive investment analysis.

Pitch Summary:
{pitch_summary}

Conversation History:
{conversation_summary}

CRITICAL: You must respond with ONLY a valid JSON object, no additional text before or after. Use this EXACT structure:

{{
    "pros": ["strength 1", "strength 2", "strength 3"],
    "cons": ["weakness 1", "weakness 2", "weakness 3"],
    "good_parts": ["what founder does well 1", "what founder does well 2"],
    "bad_parts": ["needs improvement 1", "needs improvement 2"],
    "risk_assessment": {{
        "technical_risk": "Low/Medium/High: description",
        "market_risk": "Low/Medium/High: description",
        "team_risk": "Low/Medium/High: description",
        "financial_risk": "Low/Medium/High: description",
        "regulatory_risk": "Low/Medium/High: description"
    }},
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "overall_verdict": "One sentence investment recommendation",
    "investment_score": 7
}}

Provide at least 3 items in each list. Be specific and actionable."""

        messages = [
            {"role": "system", "content": "You are an expert investment analyst. Respond ONLY with valid JSON, no markdown, no additional text."},
            {"role": "user", "content": analysis_prompt}
        ]

        response_text = mistral_client.call_openrouter_api(messages, temperature=0.3)
        logger.info(f"Raw LLM response: {response_text[:500]}")
        
        # Try to extract JSON from response
        import json
        import re
        
        # Try multiple patterns to find JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1) if json_match.lastindex else json_match.group()
            try:
                analysis_data = json.loads(json_str)
                logger.info(f"Successfully parsed JSON with keys: {list(analysis_data.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                analysis_data = {
                    "pros": ["Analysis parsing failed - raw data available"],
                    "cons": ["Unable to parse structured analysis"],
                    "good_parts": [],
                    "bad_parts": [],
                    "risk_assessment": {},
                    "recommendations": ["Contact support for manual review"],
                    "overall_verdict": "Analysis incomplete due to parsing error",
                    "investment_score": 5,
                    "raw_analysis": response_text
                }
        else:
            logger.warning("No JSON found in response")
            analysis_data = {
                "pros": ["No structured analysis generated"],
                "cons": [],
                "good_parts": [],
                "bad_parts": [],
                "risk_assessment": {},
                "recommendations": [],
                "overall_verdict": response_text[:200],
                "investment_score": 5,
                "raw_analysis": response_text
            }
        
        return {
            "analysis": analysis_data,
            "pitch_summary": req.pitch_context,
            "conversation_length": len(req.conversation_history)
        }
    except Exception as e:
        logger.error(f"Analysis generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def _update_progress(agent_name: str, status: str):
    """Update global progress state."""
    global _evaluation_progress
    _evaluation_progress[agent_name] = status


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)