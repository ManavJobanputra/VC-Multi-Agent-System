# VC Multi-Agent System - Project Structure

```
vc_multi_agent_system/
├── README.md                           # Comprehensive documentation
├── setup.sh                           # Automated setup script
├── todo.md                            # Development progress tracker
├── .env                               # Environment variables (root only - see ENVIRONMENT_SETUP.md)
├── 
├── backend/                           # FastAPI backend application
│   ├── requirements.txt              # Python dependencies
│   ├── config.py                     # Loads and validates env vars
│   ├── main.py                       # Main FastAPI application
│   ├── mistral_client.py             # Gemini (Gemma) API client
│   ├── pinecone_manager.py           # Pinecone vector database client
│   ├── rag_system.py                 # RAG implementation
│   ├── deck_processor.py             # Pitch deck (PDF/PPTX) ingestion
│   └── voice_processing.py           # Voice input/output processing
│
├── agents/                           # Multi-agent system components
│   ├── __init__.py                  # Package initialization
│   ├── base_agent.py                # Abstract base agent class
│   ├── evaluation_orchestrator.py   # Central coordinator agent
│   ├── financial_analysis_agent.py  # Financial analysis specialist
│   ├── market_analysis_agent.py     # Market analysis specialist
│   ├── risk_assessment_agent.py     # Risk assessment specialist
│   ├── team_assessment_agent.py     # Team evaluation specialist
│   ├── marcus_agent.py              # Strategic advisor agent
│   ├── execution_agent.py           # Implementation simulator agent
│   ├── answer_validation_agent.py   # Validates founder answers vs. findings
│   └── analysis_agent.py            # Comprehensive investment analysis
│
├── frontend/                        # React frontend application
│   ├── package.json                 # Node.js dependencies
│   ├── index.html                   # HTML entry point
│   ├── src/
│   │   ├── App.jsx                  # Main React component
│   │   ├── App.css                  # Application styles
│   │   ├── main.jsx                 # React entry point
│   │   ├── pages/                   # Route-level pages
│   │   └── components/              # UI components (shadcn/ui)
│   └── public/                      # Static assets
│
└── data/                            # Local scratch data (deck uploads, etc.)
```

## Key Files Description

### Backend Core Files
- **main.py**: FastAPI application with API endpoints for chat, voice, and pitch evaluation
- **config.py**: Loads and validates environment variables from the root `.env`
- **mistral_client.py**: Handles communication with the Gemini API (Gemma models)
- **pinecone_manager.py**: Manages the hosted Pinecone vector database and embeddings
- **rag_system.py**: Implements Retrieval-Augmented Generation for contextual responses
- **deck_processor.py**: Extracts text/images from uploaded pitch decks (PDF/PPTX)
- **voice_processing.py**: Handles speech-to-text and text-to-speech conversion

### Agent System Files
- **base_agent.py**: Abstract base class defining agent interface
- **evaluation_orchestrator.py**: Coordinates multi-agent evaluation process
- **financial_analysis_agent.py**: Analyzes financial aspects of pitches
- **market_analysis_agent.py**: Evaluates market opportunities and competition
- **risk_assessment_agent.py**: Identifies and assesses various risks
- **team_assessment_agent.py**: Evaluates founding team capabilities
- **marcus_agent.py**: Provides strategic mentorship and guidance
- **execution_agent.py**: Simulates implementation outcomes
- **answer_validation_agent.py**: Validates founder answers against market data and agent findings
- **analysis_agent.py**: Generates comprehensive investment analysis from conversation history

### Frontend Files
- **App.jsx**: Main React component with chat interface and pitch evaluation
- **App.css**: Tailwind CSS styling with custom theme variables
- **components/ui/**: Pre-built UI components from shadcn/ui library

### Configuration Files
- **.env**: Environment variables for API keys and configuration
- **requirements.txt**: Python package dependencies
- **package.json**: Node.js package dependencies and scripts
- **setup.sh**: Automated installation and setup script

