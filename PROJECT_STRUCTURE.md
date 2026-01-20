# VC Multi-Agent System - Project Structure

```
vc_multi_agent_system/
├── README.md                           # Comprehensive documentation
├── setup.sh                           # Automated setup script
├── todo.md                            # Development progress tracker
├── 
├── backend/                           # Flask backend application
│   ├── .env                          # Environment variables
│   ├── requirements.txt              # Python dependencies
│   ├── main.py                       # Main Flask application
│   ├── mistral_client.py            # Mistral AI API client
│   ├── qdrant_client.py             # Qdrant vector database client
│   ├── rag_system.py                # RAG implementation
│   └── voice_processing.py          # Voice input/output processing
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
│   └── execution_agent.py           # Implementation simulator agent
│
├── frontend/                        # React frontend application
│   └── vc-frontend/                 # React app directory
│       ├── package.json             # Node.js dependencies
│       ├── index.html               # HTML entry point
│       ├── src/
│       │   ├── App.jsx              # Main React component
│       │   ├── App.css              # Application styles
│       │   ├── main.jsx             # React entry point
│       │   └── components/          # UI components (shadcn/ui)
│       └── public/                  # Static assets
│
└── data/                            # Data storage directory
    └── (Vector embeddings and cached data)
```

## Key Files Description

### Backend Core Files
- **main.py**: Flask application with API endpoints for chat, voice, and pitch evaluation
- **mistral_client.py**: Handles communication with Mistral AI API
- **qdrant_client.py**: Manages vector database operations and embeddings
- **rag_system.py**: Implements Retrieval-Augmented Generation for contextual responses
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

### Frontend Files
- **App.jsx**: Main React component with chat interface and pitch evaluation
- **App.css**: Tailwind CSS styling with custom theme variables
- **components/ui/**: Pre-built UI components from shadcn/ui library

### Configuration Files
- **.env**: Environment variables for API keys and configuration
- **requirements.txt**: Python package dependencies
- **package.json**: Node.js package dependencies and scripts
- **setup.sh**: Automated installation and setup script

