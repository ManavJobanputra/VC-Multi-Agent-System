# VentureMind — Complete Project Flow

> A detailed end-to-end walkthrough of how the VentureMind multi-agent VC pitch analysis system works, from the moment a user opens the app to the final investment analysis report.

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Tech Stack](#2-tech-stack)
3. [System Components — What Does What](#3-system-components--what-does-what)
4. [Complete User Journey (Step-by-Step)](#4-complete-user-journey-step-by-step)
   - [Phase 1: Persona Selection](#phase-1-persona-selection)
   - [Phase 2: Pitch Submission & File Upload](#phase-2-pitch-submission--file-upload)
   - [Phase 3: Multi-Agent Evaluation (Loading Screen)](#phase-3-multi-agent-evaluation-loading-screen)
   - [Phase 4: Real-Time Investor Conversation](#phase-4-real-time-investor-conversation)
   - [Phase 5: End-of-Call Analysis & Report Generation](#phase-5-end-of-call-analysis--report-generation)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Agent Deep Dives](#6-agent-deep-dives)
7. [RAG Pipeline — How Context Flows](#7-rag-pipeline--how-context-flows)
8. [Voice Pipeline](#8-voice-pipeline)
9. [Session Isolation](#9-session-isolation)

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                  │
│                                                                 │
│   PersonaSelect → HomePage → LoadingScreen → ConversationUI     │
│                          ↕ HTTP (REST API)                      │
├─────────────────────────────────────────────────────────────────┤
│                        BACKEND (FastAPI / Uvicorn)              │
│                                                                 │
│   Endpoints: /evaluate_pitch, /chat, /voice_chat,               │
│              /generate_analysis, /progress, /health             │
│                          ↕                                      │
├──────────────┬──────────────┬───────────────┬───────────────────┤
│  LLM Layer   │  Vector DB   │  Agent Layer  │  Voice Layer      │
│  (OpenRouter │  (Qdrant +   │  (8 Agents)   │  (SpeechRecog +   │
│   / Mistral) │  MiniLM-L6)  │               │   gTTS)           │
└──────────────┴──────────────┴───────────────┴───────────────────┘
```

---

## 2. Tech Stack

| Layer            | Technology                                   | Purpose                                                            |
| ---------------- | -------------------------------------------- | ------------------------------------------------------------------ |
| **Frontend**     | React (Vite), shadcn/ui, Lucide icons        | UI, forms, chat interface, PDF report generation                   |
| **Backend**      | FastAPI (Python), Uvicorn                    | REST API server                                                    |
| **LLM**          | OpenRouter API → Mistral model               | Text generation, financial extraction, market analysis, validation |
| **Vision**       | OpenRouter Vision API                        | Slide image description from PPT/PDF                               |
| **Vector DB**    | Qdrant (cloud or local)                      | Embedding storage and semantic search (RAG)                        |
| **Embeddings**   | SentenceTransformer (`all-MiniLM-L6-v2`)     | Text → 384-dim vectors for Qdrant                                  |
| **Voice STT**    | Google Web Speech API (`speech_recognition`) | Audio → text transcription                                         |
| **Voice TTS**    | Google Text-to-Speech (`gTTS`)               | Text → audio response                                              |
| **Deck Parsing** | `python-pptx`, `pdfplumber`, `Pillow`        | Extract text + images from PPT/PDF files                           |
| **PDF Reports**  | jsPDF + jspdf-autotable (frontend)           | Generate downloadable investment analysis PDFs                     |

---

## 3. System Components — What Does What

### Backend Files

| File                          | Role                                                                                                                                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `backend/main.py`             | **Central orchestrator**. FastAPI app with all endpoints. Initializes all agents, manages session state, handles chat/voice flows, triggers evaluations, and coordinates the entire backend.                             |
| `backend/config.py`           | Loads environment variables from `.env` (OpenRouter API key, Qdrant URL, model name, server host/port).                                                                                                                  |
| `backend/mistral_client.py`   | **LLM gateway**. Wraps all calls to OpenRouter's chat completions API (text + vision). Handles retries (3 attempts with exponential backoff), response parsing, and error handling.                                      |
| `backend/qdrant_manager.py`   | **Vector database manager**. Connects to Qdrant (cloud or local fallback), creates collections, embeds text with SentenceTransformer, upserts data points, and performs semantic search with optional session filtering. |
| `backend/rag_system.py`       | **RAG pipeline**. Combines Qdrant retrieval with LLM generation — retrieves relevant documents, injects them as context, and generates augmented responses.                                                              |
| `backend/deck_processor.py`   | **Pitch deck parser**. Extracts text and images from `.pptx` and `.pdf` files. Sends slide images to the Vision LLM for descriptions. Builds structured page documents for indexing.                                     |
| `backend/voice_processing.py` | **Voice handler**. Transcribes audio (base64 → text via Google Speech Recognition) and generates audio responses (text → base64 MP3 via gTTS).                                                                           |

### Agents

| Agent                        | File                                 | Role                                                                                                                                                                                                                                                                                                      |
| ---------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Evaluation Orchestrator**  | `agents/evaluation_orchestrator.py`  | Central coordinator. Ingests pitch data, runs all specialist agents in order, collects results, and generates overall feedback.                                                                                                                                                                           |
| **Financial Analysis Agent** | `agents/financial_analysis_agent.py` | Uses LLM to extract financial data (revenue model, burn rate, funding ask, projections) from pitch text. Calculates runway, growth multiples, revenue quality, and health scores.                                                                                                                         |
| **Market Analysis Agent**    | `agents/market_analysis_agent.py`    | **Most complex agent**. Generates research questions from the pitch, rewrites them as search queries, scrapes the web (Bing), fetches pages in parallel, extracts market signals via LLM, estimates TAM, and stores findings in Qdrant.                                                                   |
| **Risk Assessment Agent**    | `agents/risk_assessment_agent.py`    | Deterministic risk scoring across 5 dimensions: technological, market, execution, financial, and regulatory. Produces severity ratings and mitigation strategies.                                                                                                                                         |
| **Team Assessment Agent**    | `agents/team_assessment_agent.py`    | Evaluates founder experience, team completeness, leadership strength, scaling readiness, and hiring gaps based on team size and stage.                                                                                                                                                                    |
| **Execution Agent**          | `agents/execution_agent.py`          | Simulates execution outcomes and feasibility of recommendations. Provides practical implementation insights.                                                                                                                                                                                              |
| **Marcus Agent**             | `agents/marcus_agent.py`             | **Senior strategic advisor**. Embodies the selected investor persona. Synthesizes ALL other agent results into a chain-of-thought strategic evaluation with sections: Real Opportunity, Critical Red Flags, Founder Assessment, Required Milestones, and Investment Thesis. Uses RAG context from Qdrant. |
| **Answer Validation Agent**  | `agents/answer_validation_agent.py`  | **Real-time fact-checker**. During the chat conversation, validates each founder answer against agent findings and pitch data stored in Qdrant. Classifies answers as ACCURATE, VAGUE, OPTIMISTIC, or CONTRADICTORY. Recommends next action (follow-up or new topic).                                     |
| **Analysis Agent**           | `agents/analysis_agent.py`           | **Post-conversation analyst**. After the conversation ends, retrieves all Q&A pairs, agent analyses, and validations from Qdrant. Generates a comprehensive JSON investment analysis with pros, cons, risk assessment, recommendations, verdict, and investment score (1-10).                             |

### Frontend Files

| File                                           | Role                                                                                                                                                                                                                                                                        |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `frontend/src/App.jsx`                         | **Root component & state machine**. Manages page navigation (`persona` → `home` → `loading` → `conversation`), holds global state (selected persona, pitch data, session ID, evaluation results). Handles file-to-base64 conversion and the `/evaluate_pitch` API call.     |
| `frontend/src/pages/PersonaSelect.jsx`         | Displays investor persona cards (Aarav Mehta, Vikram Khanna). User selects one to define the Marcus Agent's behavior.                                                                                                                                                       |
| `frontend/src/pages/HomePage.jsx`              | Pitch submission form with fields: Company Name, Industry, Founded Year, Team Size, Current Stage, Funding Amount, Problem Statement, Solution, Traction, Competitive Advantage, and a PPT/PDF file upload.                                                                 |
| `frontend/src/components/LoadingScreen.jsx`    | Real-time evaluation progress screen. Shows 8 animated steps with live agent progress polling from `/progress` endpoint, or auto-advancing fallback.                                                                                                                        |
| `frontend/src/pages/ConversationInterface.jsx` | **Main interaction screen**. Full chat UI with text input and voice recording. Handles `/chat` and `/voice_chat` API calls. Detects conversation end signals. Triggers `/generate_analysis` on call end. Shows `AnalysisResults` with investment analysis and PDF download. |
| `frontend/src/utils/reportGenerator.js`        | Generates a professional PDF report from the analysis data using jsPDF with investment scores, risk matrices, recommendations, etc.                                                                                                                                         |

### Personas

| File                        | Persona                                                                                                                      |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `personas/Aarav-Mehta.md`   | **High-conviction VC** — calm, measured, pattern-driven, clarity-obsessed. Asks "Why now?" and "What happens if this fails?" |
| `personas/Vikram-Khanna.md` | **Brutally honest VC** — blunt, sarcastic, zero cushioning. Says "This doesn't make sense" and "Convince me I'm wrong."      |

---

## 4. Complete User Journey (Step-by-Step)

### Phase 1: Persona Selection

**What the user sees:** A page with investor persona cards (Aarav Mehta, Vikram Khanna, Coming Soon).

**What happens:**

1. User opens the app → `App.jsx` renders `PersonaSelect` page (`currentPage = 'persona'`)
2. User clicks on a persona card → `selectedId` state updates
3. User clicks "Continue with Selected Persona" → `handleContinue()` fires
4. The full persona object (name, title, description, traits, style) is passed to `App.jsx` via `onPersonaSelect(persona)`
5. `App.jsx` stores the persona in `selectedPersona` state and sets `currentPage = 'home'`

**Why it matters:** The selected persona dictates how the **Marcus Agent** will behave — its tone, priorities, evaluation framework, and communication style during the strategic feedback phase.

---

### Phase 2: Pitch Submission & File Upload

**What the user sees:** A form to enter startup details + an optional PPT/PDF file upload.

**What happens:**

1. `App.jsx` renders `HomePage` (the pitch submission form)
2. User fills in the form fields:
   - Company Name, Industry, Founded Year, Team Size
   - Current Stage, Funding Amount
   - Problem Statement, Solution, Traction, Competitive Advantage
3. User optionally uploads a `.pptx` or `.pdf` pitch deck via the file input
4. User clicks "Submit Pitch" → `handleSubmit()` fires in `HomePage`
5. `HomePage` calls `onSubmit({ formData, file })` which triggers `handlePitchSubmit()` in `App.jsx`

**What happens in `App.jsx` → `handlePitchSubmit()`:**

```
Step 1: Set page to 'loading' → show LoadingScreen
Step 2: If file exists, convert to Base64 via FileReader
Step 3: Build the payload:
        {
          pitch_data: {
            content: "problemStatement\n\nsolution\n\ntraction",
            company_name, industry, stage,
            pitch_file_name: "deck.pptx",
            pitch_file_base64: "base64string..."
          },
          persona: selectedPersona
        }
Step 4: Start polling /progress every 500ms for agent progress updates
Step 5: POST to /evaluate_pitch with the payload
Step 6: Wait for response...
```

---

### Phase 3: Multi-Agent Evaluation (Loading Screen)

**What the user sees:** An animated loading screen showing 8 evaluation steps with a progress bar, updating in real-time as agents complete.

**What happens on the backend (`POST /evaluate_pitch`):**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. GENERATE SESSION ID                                          │
│    → A unique UUID is created for this entire pitch session      │
│    → All data stored in Qdrant is tagged with this session_id   │
│                                                                 │
│ 2. PROCESS PITCH FILE (deck_processor.py)                       │
│    → If file is provided, decode base64 → raw bytes             │
│    → If .pptx:                                                  │
│       • python-pptx opens the presentation                      │
│       • For each slide:                                         │
│         - Extract all text from shapes                          │
│         - Extract embedded images                               │
│         - Send images to Vision LLM for descriptions            │
│         - Combine text + image descriptions → page content      │
│    → If .pdf:                                                   │
│       • pdfplumber opens the PDF                                │
│       • For each page:                                          │
│         - Extract text                                          │
│         - Crop and render images                                │
│         - Send images to Vision LLM for descriptions            │
│         - Combine text + image descriptions → page content      │
│    → Result: List of {page_number, content, has_images}         │
│                                                                 │
│ 3. INDEX IN QDRANT                                              │
│    → Build page documents with metadata (company, founder, etc) │
│    → Embed each page's text with SentenceTransformer            │
│    → Upsert to Qdrant with session_id tag                       │
│                                                                 │
│ 4. RUN EVALUATION ORCHESTRATOR                                  │
│    → orchestrator.ingest_pitch(pitch_data) → wraps pitch data   │
│    → orchestrator.coordinate_evaluation() runs agents IN ORDER: │
│                                                                 │
│    ┌──────────────────────────────────────────────────┐         │
│    │ Agent 1: Financial Analysis Agent                │         │
│    │  → LLM extracts: revenue model, burn rate,       │         │
│    │    funding ask, projections from pitch text      │         │
│    │  → Calculates: runway, growth multiple,          │         │
│    │    revenue quality, financial health score       │         │
│    │  → Reports progress → frontend updates           │         │
│    ├──────────────────────────────────────────────────┤         │
│    │ Agent 2: Market Analysis Agent                   │         │
│    │  → LLM generates 6-8 research questions          │         │
│    │  → For EACH question (in parallel):              │         │
│    │    • Rewrite into 3 Bing search queries          │         │
│    │    • Scrape 5 pages per query (parallel HTTP)    │         │
│    │    • LLM extracts market signals from pages      │         │
│    │    • Store findings in Qdrant                    │         │
│    │  → LLM estimates TAM from all signals            │         │
│    │  → Reports progress → frontend updates           │         │
│    ├──────────────────────────────────────────────────┤         │
│    │ Agent 3: Risk Assessment Agent                   │         │
│    │  → Deterministic scoring across 5 dimensions:    │         │
│    │    technological, market, execution, financial,  │         │
│    │    regulatory risk                               │         │
│    │  → Based on: stage, team size, industry,         │         │
│    │    revenue model                                 │         │
│    │  → Calculates overall risk profile               │         │
│    │  → Reports progress → frontend updates           │         │
│    ├──────────────────────────────────────────────────┤         │
│    │ Agent 4: Team Assessment Agent                   │         │
│    │  → Evaluates: founder experience, team           │         │
│    │    completeness, leadership, scaling readiness   │         │
│    │  → Identifies hiring gaps                        │         │
│    │  → Reports progress → frontend updates           │         │
│    ├──────────────────────────────────────────────────┤         │
│    │ Agent 5: Execution Agent                         │         │
│    │  → Simulates execution outcomes                  │         │
│    │  → Assesses feasibility of recommendations       │         │
│    │  → Reports progress → frontend updates           │         │
│    ├──────────────────────────────────────────────────┤         │
│    │ Agent 6: Marcus Agent (LAST)                     │         │
│    │  → Receives ALL previous agent results           │         │
│    │  → Embodies the selected investor persona        │         │
│    │  → Retrieves context docs from Qdrant            │         │
│    │  → Builds chain-of-thought prompt with:          │         │
│    │    • Persona instructions                        │         │
│    │    • Specialist insights from agents 1-5         │         │
│    │    • Pitch data + Qdrant context                 │         │
│    │  → LLM generates strategic feedback:             │         │
│    │    1. The Real Opportunity                       │         │
│    │    2. Critical Red Flags                         │         │
│    │    3. Founder Assessment                         │         │
│    │    4. What Needs to Happen                       │         │
│    │    5. Investment Thesis                          │         │
│    │  → Reports progress → frontend updates           │         │
│    └──────────────────────────────────────────────────┘         │
│                                                                 │
│ 5. STORE ALL AGENT RESULTS IN QDRANT                            │
│    → Pitch context, each agent's analysis text                  │
│    → All tagged with session_id for later retrieval             │
│    → These become the "brain" for the chat conversation         │
│                                                                 │
│ 6. RETURN RESPONSE                                              │
│    → { feedback, agent_progress, deck_pages, session_id }       │
└─────────────────────────────────────────────────────────────────┘
```

**Frontend receives the response:**

1. `App.jsx` stops progress polling
2. Stores result and session_id in state
3. Sets `currentPage = 'conversation'` → renders `ConversationInterface`

---

### Phase 4: Real-Time Investor Conversation

**What the user sees:** A chat interface where they converse with the AI investor (in persona). They can type messages or use voice recording. The investor asks ONE probing question at a time.

#### Text Chat Flow (`POST /chat`)

```
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND (ConversationInterface.jsx)                         │
│                                                              │
│ 1. User types a message and hits Send                        │
│ 2. Message added to local chat history (role: "user")        │
│ 3. POST /chat with:                                          │
│    {                                                         │
│      message: "We have $50K MRR growing 15% MoM",            │
│      history: [last 5 messages],                             │
│      pitch_context: { company_name, industry, stage },       │
│      session_id: "uuid-from-evaluation"                      │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ BACKEND (/chat endpoint in main.py)                          │
│                                                              │
│ Step 1: FIND LAST INVESTOR QUESTION                          │
│  → Scan history for the most recent assistant message        │
│  → This is the "question" that the user is answering         │
│                                                              │
│ Step 2: RAG RETRIEVAL (session-scoped)                       │
│  → Encode user's message with SentenceTransformer            │
│  → Search Qdrant for top 5 similar documents                 │
│  → Filter by session_id (only this pitch's data)             │
│  → Categorize results:                                       │
│    • agent_analyses → agent insights                         │
│    • user_message / assistant_response → past conversation   │
│    • pitch_context → pitch info                              │
│  → Build enriched context string                             │
│                                                              │
│ Step 3: ANSWER VALIDATION                                    │
│  → If there was a previous question (not first message):     │
│  → AnswerValidationAgent.validate_answer():                  │
│    a. Search Qdrant for agent findings + pitch data          │
│    b. Build validation prompt with question, answer,         │
│       agent findings, market data, pitch context             │
│    c. LLM classifies as ACCURATE / VAGUE / OPTIMISTIC /      │
│       CONTRADICTORY                                          │
│    d. Provides evidence and recommended next action          │
│       (FOLLOW_UP or NEW_QUESTION)                            │
│  → Validation result appended to RAG context                 │
│                                                              │
│ Step 4: BUILD LLM MESSAGES                                   │
│  → System prompt: "You are a sharp VC investor"              │
│  → Rules: ASK ONLY ONE QUESTION per response                 │
│  → Workflow instructions for handling validations            │
│  → Conversation history (last 5 messages)                    │
│  → Current message with RAG context + validation analysis    │
│                                                              │
│ Step 5: CALL LLM (OpenRouter / Mistral)                      │
│  → MistralClient.call_openrouter_api(messages)               │
│  → Returns investor's response with ONE follow-up question   │
│                                                              │
│ Step 6: STORE Q&A IN QDRANT                                  │
│  → Store: user message, assistant response, Q&A pair,        │
│    validation result (all tagged with session_id)            │
│  → These become retrievable context for future messages      │
│                                                              │
│ Step 7: CHECK FOR CONVERSATION END                           │
│  → Separate LLM call to decide: "Do I have enough info       │
│    across revenue, unit economics, TAM, traction,            │
│    competitive positioning, team, and PMF?"                  │
│  → Returns "END_CONVERSATION" or "CONTINUE"                  │
│                                                              │
│ Step 8: RETURN RESPONSE                                      │
│  → { response, conversation_ended, end_reason, session_id }  │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND processes response                                  │
│                                                              │
│ 1. Add assistant message to chat history                     │
│ 2. Display response with typing animation effect             │
│ 3. If conversation_ended → show "End Call" prompt            │
│ 4. Otherwise → user types next answer                        │
│                                                              │
│ LOOP continues until conversation ends                       │
└──────────────────────────────────────────────────────────────┘
```

#### Voice Chat Flow (`POST /voice_chat`)

```
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND                                                     │
│ 1. User clicks mic button → browser MediaRecorder starts     │
│ 2. User speaks → audio chunks collected                      │
│ 3. User clicks stop → audio blob created (WAV)               │
│ 4. Blob → base64 string                                      │
│ 5. POST /voice_chat with { audio: base64, history, ... }     │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ BACKEND (/voice_chat endpoint)                               │
│                                                              │
│ 1. VoiceProcessor.transcribe_audio(base64)                   │
│    → Decode base64 → audio bytes                             │
│    → speech_recognition → Google Web Speech API              │
│    → Returns transcribed text                                │
│                                                              │
│ 2. RAG retrieval (same as text chat, session-scoped)         │
│                                                              │
│ 3. Build LLM messages (voice-optimized system prompt)        │
│    → Shorter responses ("1-2 sentences max")                 │
│    → More direct, impactful questions                        │
│                                                              │
│ 4. Call LLM → get investor response text                     │
│                                                              │
│ 5. VoiceProcessor.generate_audio(response_text)              │
│    → gTTS converts text → MP3                                │
│    → MP3 → base64 string                                     │
│                                                              │
│ 6. Store in Qdrant (tagged as voice messages)                │
│                                                              │
│ 7. Return { response_audio: base64, response_text }          │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND                                                     │
│ 1. Decode base64 audio → play via browser Audio API          │
│ 2. Display transcribed text in chat                          │
└──────────────────────────────────────────────────────────────┘
```

---

### Phase 5: End-of-Call Analysis & Report Generation

**What happens when the conversation ends:**

The conversation can end in two ways:

- **Auto-end:** The LLM's end-check determines it has gathered enough information (`conversation_ended: true`)
- **Manual end:** User clicks the "End Call" button

```
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND (ConversationInterface.jsx — handleEndCall())       │
│                                                              │
│ 1. POST /generate_analysis with:                             │
│    {                                                         │
│      pitch_context: {                                        │
│        companyName, industry, currentStage,                  │
│        problemStatement, solution, traction, sessionId       │
│      },                                                      │
│      conversation_history: [all chat messages]               │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ BACKEND (/generate_analysis endpoint)                        │
│                                                              │
│ → AnalysisAgent.generate_investment_analysis():              │
│                                                              │
│   Step 1: RETRIEVE Q&A PAIRS from Qdrant                     │
│    → Search for "Q&A pairs {company_name}"                   │
│    → Filter by session_id                                    │
│    → Get up to 30 Q&A pairs with validations                 │
│                                                              │
│   Step 2: RETRIEVE AGENT ANALYSES from Qdrant                │
│    → Search for "agent analysis {company_name}"              │
│    → Filter by session_id                                    │
│    → Get specialist agent findings                           │
│                                                              │
│   Step 3: RETRIEVE ANSWER VALIDATIONS from Qdrant            │
│    → Search for "answer validation"                          │
│    → Filter by session_id                                    │
│    → Get all validation results                              │
│                                                              │
│   Step 4: BUILD COMPREHENSIVE PROMPT                         │
│    → Combine: pitch context + Q&A pairs (top 15)             │
│      + agent findings (top 5) + validations (top 5)          │
│    → Request structured JSON output (investment report)      │
│                                                              │
│   Step 5: LLM GENERATES STRUCTURED ANALYSIS                  │
│    → Outputs JSON with:                                      │
│      {                                                       │
│        pros: [...],                                          │
│        cons: [...],                                          │
│        good_parts: [...],                                    │
│        bad_parts: [...],                                     │
│        risk_assessment: {                                    │
│          technical_risk, market_risk, team_risk,             │
│          financial_risk, regulatory_risk                     │
│        },                                                    │
│        recommendations: [...],                               │
│        overall_verdict: "Pass / Watch / Follow / Lead",      │
│        investment_score: 1-10                                │
│      }                                                       │
│                                                              │
│   Step 6: VALIDATE & RETURN                                  │
│    → Parse JSON, apply defaults for missing fields           │
│    → Return analysis result                                  │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND (AnalysisResults component)                         │
│                                                              │
│ 1. Display investment score (1-10) with color coding         │
│ 2. Show risk assessment matrix (5 dimensions)                │
│ 3. Show pros/cons, strengths/weaknesses                      │
│ 4. Show recommendations list                                 │
│ 5. Show overall verdict with recommendation                  │
│ 6. "Download PDF Report" button:                             │
│    → reportGenerator.js generates a professional PDF         │
│    → Uses jsPDF: cover page, executive summary, sections     │
│    → Auto-downloads to user's machine                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Diagrams

### Complete Data Pipeline

```
User Upload (PPT/PDF)
     │
     ▼
[Base64 Encode] ──→ Frontend (FileReader)
     │
     ▼
POST /evaluate_pitch
     │
     ├──→ [Deck Processor]
     │      ├──→ python-pptx / pdfplumber (text extraction)
     │      └──→ Vision LLM (image description)
     │              │
     │              ▼
     │      Page Documents [{page_number, content, has_images}]
     │              │
     │              ▼
     ├──→ [Qdrant Manager]
     │      ├──→ SentenceTransformer (embed text → 384-dim vectors)
     │      └──→ Qdrant.upsert (store with session metadata)
     │
     ├──→ [Evaluation Orchestrator]
     │      ├──→ Financial Analysis Agent (LLM extraction)
     │      ├──→ Market Analysis Agent (web scraping + LLM)
     │      ├──→ Risk Assessment Agent (deterministic scoring)
     │      ├──→ Team Assessment Agent (deterministic scoring)
     │      ├──→ Execution Agent (simulation)
     │      └──→ Marcus Agent (LLM chain-of-thought + persona)
     │              │
     │              ▼
     │      All results stored in Qdrant (session-scoped)
     │
     ▼
Response → Frontend → Conversation Phase
     │
     ├──→ /chat loop:
     │      User message → RAG retrieval → Answer Validation → LLM → Response
     │      All Q&A pairs stored in Qdrant with validations
     │
     ├──→ /voice_chat loop:
     │      Audio → STT → RAG → LLM → TTS → Audio Response
     │
     ▼
End of Call
     │
     ▼
POST /generate_analysis
     │
     ├──→ Retrieve Q&A pairs from Qdrant
     ├──→ Retrieve Agent Analyses from Qdrant
     ├──→ Retrieve Validations from Qdrant
     └──→ LLM generates structured investment analysis
              │
              ▼
     Analysis Results displayed + PDF downloadable
```

---

## 6. Agent Deep Dives

### Financial Analysis Agent — How It Works

```
1. Receives pitch text content
2. Sends to LLM with extraction prompt:
   "Extract: revenue_model, funding_ask, burn_rate,
    profitability_timeline, current_revenue,
    projected_revenue_year1, projected_revenue_year3"
3. Parses JSON response
4. Normalizes values (handles "500K", "2M" formats)
5. Calculates:
   • Runway = funding_ask / burn_rate (months)
   • Growth Multiple = year3_revenue / year1_revenue
   • Revenue Quality = "High" if SaaS/subscription, else "Medium"
6. Generates risk flags:
   • Runway < 9 months → financing risk
   • Growth < 3x → conservative projections
7. Overall health: Strong / Moderate / Weak
```

### Market Analysis Agent — How It Works

```
1. LLM generates 6-8 research questions from pitch
2. For EACH question (6 parallel workers):
   a. LLM rewrites into 3 Bing search queries
   b. For EACH query (10 parallel workers):
      • HTTP GET to Bing → parse search results
      • Extract up to 5 URLs per query
   c. For ALL URLs (30 parallel workers):
      • HTTP GET each page → strip HTML → extract text
   d. LLM extracts structured signals:
      { market_numbers, growth_rates, competitors,
        pricing_models, customer_segments, notable_claims }
   e. Store findings in Qdrant (separate collection)
3. LLM estimates TAM from all aggregated signals
4. Returns: questions, findings, market_size_estimate
```

### Answer Validation Agent — How It Works During Chat

```
1. Triggered on every /chat call (if there was a previous question)
2. Inputs: question, founder's answer, session_id, pitch_context
3. Searches Qdrant for relevant data:
   • Agent analysis results
   • Pitch document content
   • Previous pitch context
4. Builds validation prompt with all context
5. LLM produces:
   • VALIDATION STATUS: ACCURATE / VAGUE / OPTIMISTIC / CONTRADICTORY
   • EVIDENCE: specific reasons for the classification
   • RECOMMENDED NEXT ACTION: FOLLOW_UP or NEW_QUESTION
   • SUGGESTED NEXT QUESTION: exact question text
6. This validation is injected into the main chat LLM's context
   → Influences whether the investor follows up or moves on
```

---

## 7. RAG Pipeline — How Context Flows

### What Gets Stored in Qdrant

| Data Type           | When Stored                                 | Metadata Tags                                                              |
| ------------------- | ------------------------------------------- | -------------------------------------------------------------------------- |
| Pitch deck pages    | During `/evaluate_pitch` (deck processing)  | `type: "pitch_document"`, `session_id`, `page_number`                      |
| Pitch context       | During `/evaluate_pitch` (after agents run) | `type: "pitch_context"`, `session_id`, `company_name`                      |
| Agent analyses      | During `/evaluate_pitch` (after each agent) | `type: "agent_analysis"`, `session_id`, `agent` name                       |
| User messages       | During `/chat` and `/voice_chat`            | `type: "user_message"` or `"user_voice_message"`, `session_id`             |
| Assistant responses | During `/chat` and `/voice_chat`            | `type: "assistant_response"` or `"assistant_voice_response"`, `session_id` |
| Q&A pairs           | During `/chat`                              | `type: "qa_pair"`, `session_id`, full `qa_data`                            |
| Answer validations  | During `/chat` (when validation runs)       | `type: "answer_validation"`, `session_id`, question, answer                |
| Market research     | During Market Analysis Agent run            | `type: "market_research"`, question, company info                          |

### How Data Is Retrieved

Every `/chat` and `/voice_chat` call:

1. User's message is embedded with SentenceTransformer
2. Qdrant semantic search finds top 5 most similar documents
3. Results are **filtered by session_id** (only this pitch's data)
4. Results are categorized (agent analysis / conversation / pitch context)
5. Organized into enriched context and injected into the LLM prompt

---

## 8. Voice Pipeline

```
                      ┌────────────┐
  User speaks ──────→ │ Browser    │ ──→ MediaRecorder captures audio
                      │ Microphone │      (WAV format, audio chunks)
                      └────────────┘
                            │
                            ▼
                    [Blob → Base64]
                            │
                            ▼
              POST /voice_chat { audio: base64 }
                            │
                            ▼
              ┌─────────────────────────┐
              │ VoiceProcessor          │
              │ .transcribe_audio()     │
              │                         │
              │ base64 → bytes          │
              │ bytes → AudioFile       │
              │ speech_recognition      │
              │   → Google Web Speech   │
              │   → "transcribed text"  │
              └─────────────────────────┘
                            │
                            ▼
              (Same as text chat: RAG + LLM → response)
                            │
                            ▼
              ┌─────────────────────────┐
              │ VoiceProcessor          │
              │ .generate_audio()       │
              │                         │
              │ response text → gTTS    │
              │ gTTS → MP3 bytes        │
              │ MP3 → base64 string     │
              └─────────────────────────┘
                            │
                            ▼
              Response: { response_audio: base64, response_text }
                            │
                            ▼
              Frontend decodes base64 → plays audio
              + displays text in chat
```

---

## 9. Session Isolation

Every pitch evaluation creates a **unique session_id** (UUID). This ID is used to:

1. **Tag all Qdrant documents** — pitch pages, agent results, chat messages, validations
2. **Filter Qdrant searches** — every search includes a `session_filter` so only this pitch's data is retrieved
3. **Track conversation state** — the frontend passes `session_id` with every `/chat` and `/voice_chat` call
4. **Scope final analysis** — the Analysis Agent retrieves only this session's Q&A pairs and agent findings

This ensures that:

- Multiple users can evaluate different pitches simultaneously
- Data from one pitch evaluation never leaks into another
- The investor's questions are always grounded in the correct pitch's data

---

## Summary: The Complete Lifecycle

```
1. SELECT PERSONA         → Defines investor behavior
2. SUBMIT PITCH + DECK    → Frontend sends form data + base64 file
3. DECK PROCESSING        → Extract text + images, Vision LLM describes slides
4. QDRANT INDEXING        → Embed and store all pitch content
5. MULTI-AGENT EVAL       → 6 agents analyze in sequence (Financial → Market → Risk → Team → Execution → Marcus)
6. STORE RESULTS          → All agent outputs stored in Qdrant per session
7. CONVERSATION BEGINS    → User chats with AI investor (text or voice)
8. PER-MESSAGE LOOP:
   a. RAG retrieval (session-scoped)
   b. Answer validation (against agent findings)
   c. LLM generates ONE probing question
   d. Store Q&A + validation in Qdrant
   e. Check if enough info gathered
9. CONVERSATION ENDS      → Auto (LLM decides) or manual (user clicks)
10. ANALYSIS GENERATION   → Retrieve all Q&A, agents, validations from Qdrant → LLM produces structured JSON report
11. RESULTS DISPLAYED     → Investment score, risks, pros/cons, verdict
12. PDF DOWNLOAD          → Professional report generated client-side
```
