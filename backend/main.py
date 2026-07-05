import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Load configuration from .env
from config import HOST, PORT, DEBUG, SELF_PING_URL, SELF_PING_INTERVAL_MINUTES, SELF_PING_ENABLED

from mistral_client import MistralClient
from pinecone_manager import PineconeManager
from rag_system import RAGSystem
from deck_processor import process_pitch_file, build_page_documents
from scheduler import SelfPingScheduler
from admin_auth import verify_password, create_session, verify_session
from env_editor import read_env_masked, update_env
from db import init_db
import user_auth
import billing
import session_store
from agents.evaluation_orchestrator import EvaluationOrchestrator
from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.team_assessment_agent import TeamAssessmentAgent
from agents.marcus_agent import MarcusAgent
from agents.execution_agent import ExecutionAgent
from agents.answer_validation_agent import AnswerValidationAgent
from agents.analysis_agent import AnalysisAgent
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
    session_id: Optional[str] = None


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
# Shared singletons - each PineconeManager() call loads its own copy of the
# embedding model and describes/connects to the Pinecone index, so every
# agent that needs one gets the same shared instance rather than
# constructing its own (was 5 separate embedding-model loads on every boot).
pinecone_manager = PineconeManager()
pinecone_manager_market = PineconeManager(collection_name="vc_pitches_market")
rag_system = RAGSystem(pinecone_manager, mistral_client)
voice_processor = VoiceProcessor()

# Initialize agents
agents = {
    "evaluation_orchestrator": EvaluationOrchestrator(),
    "financial_analysis_agent": FinancialAnalysisAgent(),
    "market_analysis_agent": MarketAnalysisAgent(pinecone_manager=pinecone_manager_market),
    "risk_assessment_agent": RiskAssessmentAgent(),
    "team_assessment_agent": TeamAssessmentAgent(),
    "marcus_agent": MarcusAgent(pinecone_manager=pinecone_manager),
    "execution_agent": ExecutionAgent(),
    "answer_validation_agent": AnswerValidationAgent(pinecone_manager=pinecone_manager),
    "analysis_agent": AnalysisAgent(pinecone_manager=pinecone_manager)
}

# Global state for progress tracking
_evaluation_progress = {}
_conversation_history = {}  # Store conversation per session
_evaluation_results = {}  # Store evaluation results for analysis

# Self-ping keep-alive scheduler
self_ping_scheduler = SelfPingScheduler(
    url=SELF_PING_URL,
    interval_minutes=SELF_PING_INTERVAL_MINUTES,
    enabled=SELF_PING_ENABLED,
)
self_ping_scheduler.start()

# Users/credits/payments DB (SQLite for now - see db.py for the caveat
# about moving to hosted Postgres before real deployment)
init_db()


def require_admin(authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
    if not verify_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_user(authorization: Optional[str] = Header(None)) -> str:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
    email = user_auth.get_session_email(token)
    if not email:
        raise HTTPException(status_code=401, detail="Sign in required")
    return email


class AdminLoginRequest(BaseModel):
    password: str


class CronToggleRequest(BaseModel):
    enabled: bool


class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, str]


@app.post("/admin/login")
def admin_login(req: AdminLoginRequest):
    if not verify_password(req.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"token": create_session()}


@app.get("/admin/status")
def admin_status(_: None = Depends(require_admin)):
    return {
        "cron": self_ping_scheduler.status(),
        "config": read_env_masked(),
    }


@app.post("/admin/cron/toggle")
def admin_cron_toggle(req: CronToggleRequest, _: None = Depends(require_admin)):
    self_ping_scheduler.set_enabled(req.enabled)
    return self_ping_scheduler.status()


@app.post("/admin/config")
def admin_update_config(req: ConfigUpdateRequest, _: None = Depends(require_admin)):
    update_env(req.updates)
    return {
        "status": "saved",
        "note": "Saved to .env. Restart the server for these changes to take effect.",
        "config": read_env_masked(),
    }


class RequestLinkRequest(BaseModel):
    email: str


class VerifyLinkRequest(BaseModel):
    token: str


class CreateOrderRequest(BaseModel):
    pack: str


@app.post("/auth/request-link")
def auth_request_link(req: RequestLinkRequest):
    if not user_auth.is_valid_email(req.email):
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    user_auth.request_magic_link(req.email)
    return {"status": "sent"}


@app.post("/auth/verify")
def auth_verify(req: VerifyLinkRequest):
    email = user_auth.verify_magic_link(req.token)
    if not email:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired")
    session_token = user_auth.create_session(email)
    user = user_auth.get_user(email)
    return {"token": session_token, "user": user}


@app.get("/me")
def me(email: str = Depends(require_user)):
    return user_auth.get_user(email)


@app.get("/sessions")
def list_sessions(email: str = Depends(require_user)):
    return session_store.get_user_sessions(email)


@app.get("/sessions/{session_id}")
def get_session(session_id: str, email: str = Depends(require_user)):
    detail = session_store.get_session_detail(session_id, email)
    if detail is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail


@app.post("/billing/create-order")
def billing_create_order(req: CreateOrderRequest, email: str = Depends(require_user)):
    if req.pack not in billing.CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Unknown credit pack")
    try:
        return billing.create_order(email, req.pack)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/billing/packs")
def billing_packs():
    return billing.CREDIT_PACKS


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not billing.verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event = await request.json()
    if event.get("event") == "payment.captured":
        payment_entity = event["payload"]["payment"]["entity"]
        billing.handle_payment_captured(
            order_id=payment_entity["order_id"],
            payment_id=payment_entity["id"],
        )
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest, email: str = Depends(require_user)):
    if not req.message:
        raise HTTPException(status_code=400, detail="No message provided")

    # Get or create session ID
    session_id = req.session_id or str(uuid4())

    if req.session_id:
        if not session_store.owns_session(session_id, email):
            raise HTTPException(status_code=403, detail="This session does not belong to you")
    else:
        # Defensive fallback - the real flow always creates the session
        # via /evaluate_pitch first, but avoid silently orphaning a chat
        # that somehow arrives without one.
        session_store.create_session(session_id, email, req.pitch_context or {}, None)
    
    # Build context from pitch and history
    context_prompt = ""
    if req.pitch_context:
        context_prompt = f"Context: Company {req.pitch_context.get('company_name')}, {req.pitch_context.get('industry')}, Stage: {req.pitch_context.get('stage')}\n"
    
    # Extract last question asked (if any) from history
    last_question = None
    for msg in reversed(req.history[-5:]):
        if msg.get('role') == 'assistant':
            last_question = msg.get('content', '')
            break
    
    # Prepare RAG context from conversation history and agent analyses - FILTER BY SESSION
    rag_query = req.message
    rag_results = pinecone_manager.search(rag_query, limit=5, session_filter=session_id)
    
    # Organize RAG results by type for better context
    agent_analyses = []
    conversation_context = []
    pitch_context_items = []
    
    for doc in rag_results:
        payload = doc.get('payload', {})
        doc_type = payload.get('type', 'unknown')
        content = payload.get('content', '')
        
        if doc_type == 'agent_analysis':
            agent_analyses.append({
                'agent': payload.get('agent', 'Unknown Agent'),
                'content': content
            })
        elif doc_type in ['user_message', 'assistant_response', 'user_voice_message', 'assistant_voice_response']:
            conversation_context.append(content)
        elif doc_type == 'pitch_context':
            pitch_context_items.append(content)
    
    # Build enriched context prompt
    enriched_context = ""
    if pitch_context_items:
        enriched_context += "PITCH CONTEXT:\n" + "\n".join(pitch_context_items) + "\n\n"
    
    if agent_analyses:
        enriched_context += "INSIGHTS FROM SPECIALIST AGENTS:\n"
        for analysis in agent_analyses:
            enriched_context += f"- {analysis['agent']}:\n{analysis['content']}\n"
        enriched_context += "\n"
    
    if conversation_context:
        enriched_context += "RELEVANT CONVERSATION INSIGHTS:\n" + "\n".join(conversation_context) + "\n"
    
    rag_context = enriched_context
    
    # Call LLM with context
    messages = [
        {
            "role": "system",
            "content": (
                "You are a sharp, experienced venture capital investor with a track record of finding unicorns. "
                "Your role is to probe deeply into the startup pitch and founder's thinking with TECHNICAL investor questions. "
                "You have access to:\n"
                "- Detailed analysis from specialist agents (Financial, Market, Risk, Team, Execution experts)\n"
                "- Real-time answer validation against market data and agent findings\n"
                "- Historical Q&A context\n\n"
                
                "⚠️ ABSOLUTE RULE - ONLY ONE QUESTION PER RESPONSE:\n"
                "You MUST ask EXACTLY ONE question. NO exceptions. NO multiple questions in one message.\n"
                "DO NOT use 'and' to combine questions. DO NOT ask follow-ups in the same message.\n"
                "ASK ONE. WAIT FOR ANSWER. THEN ASK NEXT.\n\n"
                
                "WORKFLOW:\n"
                "1. When you receive a founder's answer, you'll get VALIDATION ANALYSIS that shows:\n"
                "   - Whether answer aligns with specialist agent findings and market data\n"
                "   - If it's specific or vague\n"
                "   - If it contradicts known information\n"
                "   - Recommended next action (FOLLOW_UP or NEW_QUESTION)\n\n"
                
                "2. Based on the VALIDATION ANALYSIS provided:\n"
                "   - If validation says VAGUE/CONTRADICTORY → Ask ONE follow-up question to clarify that specific point\n"
                "   - If validation says ACCURATE but flags concerns → Challenge with ONE specific data point\n"
                "   - If validation says SOLID → Acknowledge in ONE sentence, then ask ONE NEW question\n\n"
                
                "3. FORMAT YOUR RESPONSE:\n"
                "   Option A (Follow-up): '[Brief 1-sentence acknowledgment if needed] [ONE question with ?]'\n"
                "   Option B (New topic): '[Brief acknowledgment] [ONE question on NEW topic with ?]'\n\n"
                
                "EXAMPLES OF CORRECT RESPONSES (ONLY ONE QUESTION):\n"
                "✓ 'What's your current MoM growth rate?'\n"
                "✓ 'That's concerning. What's your actual customer conversion rate?'\n"
                "✓ 'Good conversion rate. What's your CAC?'\n\n"
                
                "EXAMPLES OF INCORRECT RESPONSES (MULTIPLE QUESTIONS - NEVER DO THIS):\n"
                "✗ 'What's your MoM growth? And what about your burn rate?'\n"
                "✗ 'Tell me about your TAM. How many customers do you have?'\n"
                "✗ 'What's your CAC and LTV?'\n\n"
                
                "TECHNICAL METRICS TO PROBE (ONE AT A TIME):\n"
                "- Revenue growth rates (MoM, YoY), runway, burn rate\n"
                "- CAC, LTV, payback period\n"
                "- Unit economics, gross margins, net retention\n"
                "- TAM validation, customer traction\n"
                "- Competitive advantages, defensibility\n"
                "- Team execution risk\n\n"
                
                f"{context_prompt}"
                "REMEMBER: ONE QUESTION ONLY. Use validation analysis. Be direct but data-driven."
            ),
        },
    ]
    
    # Add conversation history
    for msg in req.history[-5:]:  # Last 5 for context window
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    
    # STEP: Validate answer using Answer Validation Agent (if there was a previous question)
    validation_result = None
    if last_question:
        try:
            validation_agent = agents["answer_validation_agent"]
            validation_result = validation_agent.validate_answer(
                question=last_question,
                answer=req.message,
                session_id=session_id,
                pitch_context=req.pitch_context or {}
            )
            logger.info(f"Answer validation completed: {validation_result.get('validation', '')[:200]}")
            
            # Add validation insights to RAG context
            if validation_result and validation_result.get('validation'):
                rag_context += f"\n\nANSWER VALIDATION ANALYSIS:\n{validation_result['validation']}\n"
        except Exception as e:
            logger.warning(f"Answer validation failed: {e}")
    
    # Add current message with RAG context and answer validation instruction
    user_content = req.message
    if last_question:
        user_content = f"[Previous Question: {last_question}]\n\n[Founder's Answer]: {req.message}"
    
    if rag_context:
        messages.append({"role": "user", "content": f"{user_content}\n\n[Retrieved Context from Analysis]:\n{rag_context}"})
    else:
        messages.append({"role": "user", "content": user_content})
    
    response_text = mistral_client.call_openrouter_api(messages)
    if not response_text.strip():
        raise HTTPException(status_code=502, detail="Failed to get a response from the AI model")

    # Store Q&A pair with validation in structured format to Chroma
    try:
        qa_pair = {
            "question": last_question or "Initial greeting",
            "answer": req.message,
            "investor_response": response_text,
            "validation": validation_result.get('validation', '') if validation_result else None,
            "validation_status": "validated" if validation_result else "not_validated",
            "timestamp": str(uuid4())[:8]
        }
        
        qa_text = f"Q: {qa_pair['question']}\nA: {qa_pair['answer']}\nInvestor: {qa_pair['investor_response']}"
        if validation_result:
            qa_text += f"\nValidation: {validation_result.get('validation', '')[:300]}"
        
        # Build metadata list for storage
        metadata_list = [
            {"type": "user_message", "conversation": True, "session_id": session_id, "content": req.message},
            {"type": "assistant_response", "conversation": True, "session_id": session_id, "content": response_text},
            {"type": "qa_pair", "session_id": session_id, "qa_data": qa_pair, "content": qa_text}
        ]
        
        # Add validation result as separate entry if available
        if validation_result and validation_result.get('validation'):
            metadata_list.append({
                "type": "answer_validation",
                "session_id": session_id,
                "question": last_question,
                "answer": req.message,
                "validation_summary": validation_result.get('validation', '')[:500],
                "content": f"Validation for '{last_question}': {validation_result.get('validation', '')}"
            })
        
        pinecone_manager.upsert_data(
            [req.message, response_text, qa_text] + ([validation_result.get('validation', '')] if validation_result else []),
            metadata_list
        )
        logger.info(f"Stored Q&A pair to Chroma for session {session_id}")
    except Exception as e:
        logger.warning(f"Could not store Q&A pair to Chroma: {e}")
    
    # Check if agent thinks they have enough info to end conversation
    history_summary = "\n".join([f"{msg.get('role')}: {msg.get('content')[:150]}..." for msg in req.history[-5:]])
    end_check_messages = [
        {
            "role": "system",
            "content": (
                "You are a venture investor deciding whether you have ENOUGH CRITICAL INFORMATION for a comprehensive investment decision.\n\n"
                "You should ONLY say 'END_CONVERSATION' if you have gathered data on MOST of these key areas:\n"
                "- Revenue/traction metrics (current ARR, MoM growth, YoY trajectory)\n"
                "- Unit economics (CAC, LTV, payback period, gross margins)\n"
                "- TAM validation (both top-down and bottom-up analysis)\n"
                "- Customer traction (actual contracts, LOIs, or strong pipeline evidence)\n"
                "- Competitive positioning and defensibility\n"
                "- Team capabilities and execution risk\n"
                "- Product-market fit indicators\n\n"
                "If you're MISSING critical metrics or data on multiple areas, reply with 'CONTINUE'\n"
                "Only reply with EXACTLY 'END_CONVERSATION' (nothing else) when you truly have enough to make a decision.\n"
                "Only reply with EXACTLY 'CONTINUE' (nothing else) when you need more info."
            )
        },
        {"role": "user", "content": f"Full conversation so far:\n{history_summary}\n\nDo you have enough information to make a comprehensive investment decision?"}
    ]
    
    end_decision = mistral_client.call_openrouter_api(end_check_messages).strip().upper()
    conversation_ended = "END_CONVERSATION" in end_decision
    
    # Store in Chroma for RAG retrieval with SESSION ID
    try:
        pinecone_manager.upsert_data(
            [req.message, response_text],
            [
                {"type": "user_message", "conversation": True, "session_id": session_id, "content": req.message},
                {"type": "assistant_response", "conversation": True, "session_id": session_id, "content": response_text}
            ]
        )
    except Exception as e:
        logger.warning(f"Could not store conversation to Chroma: {e}")

    try:
        session_store.add_message(session_id, "user", req.message)
        session_store.add_message(session_id, "assistant", response_text)
    except Exception as e:
        logger.warning(f"Could not persist messages for session history: {e}")

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
    
    # Prepare RAG context - FILTER BY SESSION (enhanced with agent analyses)
    rag_results = pinecone_manager.search(transcribed_text, limit=5, session_filter=session_id)
    
    # Organize RAG results by type for better context
    agent_analyses = []
    conversation_context = []
    pitch_context_items = []
    
    for doc in rag_results:
        payload = doc.get('payload', {})
        doc_type = payload.get('type', 'unknown')
        content = payload.get('content', '')
        
        if doc_type == 'agent_analysis':
            agent_analyses.append({
                'agent': payload.get('agent', 'Unknown Agent'),
                'content': content
            })
        elif doc_type in ['user_message', 'assistant_response', 'user_voice_message', 'assistant_voice_response']:
            conversation_context.append(content)
        elif doc_type == 'pitch_context':
            pitch_context_items.append(content)
    
    # Build enriched context prompt (keep it brief for voice)
    enriched_context = ""
    if agent_analyses:
        enriched_context += "Key insights: "
        insights = [f"{a['agent']}" for a in agent_analyses]
        enriched_context += ", ".join(insights) + ". "
    
    rag_context = enriched_context
    
    # Call LLM with context
    messages = [
        {
            "role": "system",
            "content": (
                "You are a sharp, experienced venture capital investor with a track record of finding unicorns. "
                "Your role is to probe deeply into the startup pitch and founder's thinking through voice conversation with TECHNICAL investor questions. "
                "You ask INTELLIGENT, PROBING questions that challenge assumptions and uncover hidden risks or opportunities.\n\n"
                
                "CRITICAL INSTRUCTIONS FOR VOICE:\n"
                "1. NEVER just confirm what the founder says - dig deeper with follow-ups!\n"
                "2. Ask ONE strategic question that shows you're thinking critically about their business.\n"
                "3. Focus on TECHNICAL METRICS AND INVESTOR FUNDAMENTALS:\n"
                "   - Revenue growth rates (MoM, YoY), runway, burn rate\n"
                "   - Unit economics (CAC, LTV, payback period, margins)\n"
                "   - TAM calculations and customer traction\n"
                "   - Competitive advantages and defensibility\n"
                "   - Team execution risk\n"
                "   - Product-market fit evidence\n"
                "4. Don't ask for basic info - assume you have some context already. Ask sophisticated follow-ups.\n"
                "5. Show expertise through your questions. Reference industry trends and comparable companies.\n"
                "6. Be direct and candid. Point out gaps or inconsistencies in their story.\n"
                "7. Keep responses BRIEF for voice (1-2 sentences max for questions), but impactful and specific to metrics.\n\n"
                
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
    if not response_text.strip():
        raise HTTPException(status_code=502, detail="Failed to get a response from the AI model")

    # Generate response audio
    response_audio_base64 = voice_processor.generate_audio(response_text)
    
    # Store in Chroma for RAG retrieval with SESSION ID
    try:
        pinecone_manager.upsert_data(
            [transcribed_text, response_text],
            [
                {"type": "user_voice_message", "conversation": True, "session_id": session_id, "content": transcribed_text},
                {"type": "assistant_voice_response", "conversation": True, "session_id": session_id, "content": response_text}
            ]
        )
    except Exception as e:
        logger.warning(f"Could not store voice conversation to Chroma: {e}")
    
    return {"response_audio": response_audio_base64, "response_text": response_text, "session_id": session_id}


def _store_agent_results_to_chroma(session_id: str, pitch_data: Dict, evaluation_results: Dict):
    """Store all agent evaluation results to Chroma for RAG retrieval."""
    try:
        texts_to_store = []
        metadatas_to_store = []
        
        # Store pitch context
        pitch_text = f"Pitch for {pitch_data.get('company_name', 'Unknown')}: {pitch_data.get('content', '')[:500]}"
        texts_to_store.append(pitch_text)
        metadatas_to_store.append({
            "type": "pitch_context",
            "session_id": session_id,
            "company_name": pitch_data.get("company_name"),
            "industry": pitch_data.get("industry"),
            "stage": pitch_data.get("stage"),
            "content": pitch_text
        })
        
        # Store each agent's analysis result
        for agent_name, result in evaluation_results.items():
            if isinstance(result, dict):
                # Convert result to readable text format
                agent_text = f"{agent_name.replace('_', ' ').title()} Analysis:\n"
                for key, value in result.items():
                    if isinstance(value, (str, int, float)):
                        agent_text += f"- {key}: {value}\n"
                    elif isinstance(value, list):
                        agent_text += f"- {key}: {', '.join(str(v) for v in value)}\n"
                    elif isinstance(value, dict):
                        agent_text += f"- {key}: {str(value)}\n"
                
                texts_to_store.append(agent_text)
                metadatas_to_store.append({
                    "type": "agent_analysis",
                    "agent": agent_name,
                    "session_id": session_id,
                    "company_name": pitch_data.get("company_name"),
                    "content": agent_text[:1000]
                })
        
        # Upsert to Chroma
        if texts_to_store:
            pinecone_manager.upsert_data(texts_to_store, metadatas_to_store)
            logger.info(f"Stored {len(texts_to_store)} agent result documents to Chroma for session {session_id}")
    except Exception as e:
        logger.warning(f"Could not store agent results to Chroma: {e}")


@app.post("/evaluate_pitch")
def evaluate_pitch(req: EvaluatePitchRequest, email: str = Depends(require_user)):
    if not user_auth.can_start_session(email):
        raise HTTPException(
            status_code=402,
            detail="No sessions remaining. Purchase a credit pack to start another evaluation.",
        )
    user_auth.consume_session_entitlement(email)

    global _evaluation_progress
    _evaluation_progress = {}

    # Generate unique session ID for this pitch
    session_id = str(uuid4())
    
    pitch_data = req.pitch_data.dict()
    # Optional string fields are explicitly None (not just absent) when the
    # frontend omits them, since PitchData declares them as Optional[str] =
    # None - several agents call .lower()/.strip() on these without a None
    # guard, so normalize to "" here once rather than in every agent.
    for field in ("company_name", "founder_name", "email", "industry", "stage"):
        if pitch_data.get(field) is None:
            pitch_data[field] = ""

    if not pitch_data.get("content"):
        raise HTTPException(status_code=400, detail="No pitch content provided. Please include a 'content' field in your pitch_data.")

    session_store.create_session(session_id, email, pitch_data, req.persona)

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
            pinecone_manager.upsert_data(
                [d["text"] for d in docs],
                [d["metadata"] for d in docs]
            )

    orchestrator = agents["evaluation_orchestrator"]
    processed_pitch = orchestrator.ingest_pitch(pitch_data)
    evaluation_results, progress = orchestrator.coordinate_evaluation(processed_pitch, agents, progress_callback=lambda agent_name, status: _update_progress(agent_name, status))
    
    # Store all agent results to Chroma for RAG retrieval
    _store_agent_results_to_chroma(session_id, pitch_data, evaluation_results)
    
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
def generate_analysis(req: AnalysisRequest, email: str = Depends(require_user)):
    """Generate comprehensive investment analysis using Analysis Agent."""
    try:
        if not req.pitch_context or not req.conversation_history:
            raise HTTPException(status_code=400, detail="Pitch context and conversation history required")

        # session_id MUST be a real, non-empty value here: pinecone_manager.search
        # treats a falsy session_filter (None or "") as "no filter", meaning an
        # empty/missing session_id would search across every session ever
        # stored in this namespace - pulling other users' Q&A into this memo -
        # rather than just this one. Reject rather than silently doing that.
        if not req.session_id:
            raise HTTPException(status_code=400, detail="session_id is required to scope the analysis to this session")

        if not session_store.owns_session(req.session_id, email):
            raise HTTPException(status_code=403, detail="This session does not belong to you")

        # Use Analysis Agent to generate comprehensive report
        analysis_agent = agents["analysis_agent"]
        analysis_result = analysis_agent.generate_investment_analysis(
            session_id=req.session_id,
            pitch_context=req.pitch_context,
            conversation_history=req.conversation_history
        )

        logger.info(f"Analysis generated successfully with score: {analysis_result.get('investment_score')}")

        session_store.save_analysis(req.session_id, analysis_result, analysis_result.get('investment_score'))

        return {
            "analysis": analysis_result,
            "pitch_summary": req.pitch_context,
            "conversation_length": len(req.conversation_history)
        }

    except HTTPException:
        raise
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
    if DEBUG:
        # reload=True needs an import string so uvicorn can re-import
        # fresh code on file changes.
        uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
    else:
        # Passing the app object directly (rather than the "main:app"
        # string) avoids uvicorn re-importing this module a second time,
        # which was doubling every agent's startup work (embedding model
        # loads, Pinecone index connections, etc.) on every boot.
        uvicorn.run(app, host=HOST, port=PORT)