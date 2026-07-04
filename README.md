# VC Multi-Agent System Documentation

## Overview

The VC Multi-Agent System is an AI-powered venture capital pitch evaluation platform that simulates the decision-making process of experienced venture capitalists. The system uses multiple specialized AI agents to analyze different aspects of startup pitches and provide comprehensive feedback through chat, voice, and video interactions.

## System Architecture

### Technology Stack
- **Backend**: Flask (Python)
- **Frontend**: React with Tailwind CSS
- **Database**: Qdrant (Vector Database)
- **AI Model**: Mistral AI API
- **Embeddings**: Sentence Transformers
- **Voice Processing**: SpeechRecognition + gTTS
- **Audio Handling**: Base64 encoding/decoding

### Multi-Agent Architecture

The system consists of seven specialized AI agents working in coordination:

1. **Evaluation Orchestrator**: Central coordinator and decision maker
2. **Financial Analysis Agent**: Financial health and projections analyst
3. **Market Analysis Agent**: Market opportunity and competitive landscape analyst
4. **Risk Assessment Agent**: Risk identification and mitigation strategist
5. **Team Assessment Agent**: Founding team and organizational analyst
6. **Marcus Agent**: Senior strategic advisor and mentor
7. **Execution Agent**: Implementation and outcome simulator

## Key Features

- **Real-time Analysis**: Immediate feedback on startup pitches
- **Multi-modal Interaction**: Support for text chat, voice input/output
- **Comprehensive Evaluation**: Financial, market, risk, team, and strategic analysis
- **RAG Integration**: Retrieval-Augmented Generation for contextual responses
- **Voice Processing Pipeline**: Complete audio processing with Base64 encoding
- **Responsive UI**: Modern React interface with real-time updates

## Installation and Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Qdrant database (local or cloud)
- Internet connection for Mistral API and speech services

### Backend Setup

1. Navigate to the backend directory:
```bash
cd vc_multi_agent_system/backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
`backend/config.py` only loads a `.env` file from the **project root** (not `backend/`). Copy `.env.example` to `.env` in the root folder and fill in your values - see `ENVIRONMENT_SETUP.md` for details.

4. Start Qdrant database (if running locally):
```bash
# Using Docker (if available)
docker run -p 6333:6333 qdrant/qdrant

# Or install Qdrant locally following their documentation
```

5. Run the Flask backend:
```bash
python main.py
```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd vc_multi_agent_system/frontend/vc-frontend
```

2. Install dependencies:
```bash
pnpm install
```

3. Start the development server:
```bash
pnpm run dev --host
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

### Chat Endpoint
- **URL**: `/chat`
- **Method**: POST
- **Body**: 
```json
{
  "message": "Your message here",
  "history": [{"role": "user", "content": "Previous message"}]
}
```
- **Response**: 
```json
{
  "response": "AI response"
}
```

### Voice Chat Endpoint
- **URL**: `/voice_chat`
- **Method**: POST
- **Body**: 
```json
{
  "audio": "base64_encoded_audio",
  "history": [{"role": "user", "content": "Previous message"}]
}
```
- **Response**: 
```json
{
  "response_audio": "base64_encoded_audio_response",
  "response_text": "Transcribed response text"
}
```

### Pitch Evaluation Endpoint
- **URL**: `/evaluate_pitch`
- **Method**: POST
- **Body**: 
```json
{
  "pitch_data": {
    "content": "Your startup pitch details"
  }
}
```
- **Response**: 
```json
{
  "feedback": {
    "summary": "Overall evaluation summary",
    "details": {
      "agent_name": {
        "analysis_point": "detailed analysis"
      }
    }
  }
}
```

## Usage Guide

### Text Chat
1. Open the application in your browser
2. Type your message in the chat interface
3. Press Enter or click Send to receive AI responses
4. View conversation history in the chat panel

### Voice Interaction
1. Click the microphone button to start recording
2. Speak your message clearly
3. Click the stop button to end recording
4. The system will transcribe your speech and provide audio response
5. Click the speaker icon to replay audio responses

### Pitch Evaluation
1. Navigate to the Pitch Evaluation panel
2. Enter your startup pitch details in the text area
3. Click "Evaluate Pitch" to receive comprehensive analysis
4. Review feedback from all specialized agents
5. Each agent provides specific insights in their domain

## Agent Responsibilities

### Evaluation Orchestrator
- Coordinates the evaluation process across all agents
- Manages data flow between agents
- Generates final comprehensive feedback
- Handles pitch data ingestion and processing

### Financial Analysis Agent
- Analyzes revenue projections and financial models
- Evaluates business model viability
- Assesses funding requirements and valuation
- Identifies financial risks and opportunities

### Market Analysis Agent
- Evaluates market size and growth potential
- Analyzes target audience and customer segments
- Assesses competitive landscape
- Identifies market trends and opportunities

### Risk Assessment Agent
- Identifies technological, market, and operational risks
- Evaluates regulatory and compliance challenges
- Suggests risk mitigation strategies
- Assesses overall risk profile

### Team Assessment Agent
- Evaluates founder experience and expertise
- Assesses team completeness and skill gaps
- Analyzes leadership capabilities
- Identifies team-related risks and strengths

### Marcus Agent
- Provides high-level strategic feedback
- Identifies growth opportunities and pivot potential
- Offers seasoned venture capitalist perspective
- Suggests long-term strategic direction

### Execution Agent
- Simulates execution of recommendations
- Provides realistic outcome assessments
- Evaluates implementation feasibility
- Offers practical execution insights

## Voice Processing Pipeline

The system implements a complete voice processing pipeline:

1. **Frontend Audio Capture**: Web Audio API captures microphone input
2. **Base64 Encoding**: Audio data encoded for transmission
3. **Backend Processing**: Flask receives and decodes audio
4. **Speech-to-Text**: SpeechRecognition transcribes audio to text
5. **AI Processing**: Mistral AI processes the transcribed text
6. **Text-to-Speech**: gTTS converts response to audio
7. **Base64 Response**: Audio response encoded and sent to frontend
8. **Frontend Playback**: Browser plays the audio response

## RAG System Integration

The Retrieval-Augmented Generation (RAG) system enhances responses by:

1. **Document Ingestion**: Startup pitch data stored in Qdrant
2. **Vector Embeddings**: Sentence transformers create embeddings
3. **Similarity Search**: Relevant context retrieved based on queries
4. **Context Enhancement**: Retrieved information augments AI responses
5. **Conversational Memory**: System maintains conversation context

## Troubleshooting

### Common Issues

**Backend not starting:**
- Check Python dependencies are installed
- Verify Qdrant database is running
- Ensure environment variables are set correctly

**Voice features not working:**
- Check microphone permissions in browser
- Verify internet connection for speech services
- Ensure audio format compatibility

**Frontend not connecting to backend:**
- Verify backend is running on port 5000
- Check CORS settings in Flask application
- Ensure no firewall blocking connections

**Qdrant connection issues:**
- Verify Qdrant service is running
- Check connection parameters
- Ensure proper network configuration

### Performance Optimization

- Use local Qdrant instance for better performance
- Implement caching for frequently accessed data
- Optimize embedding generation for large datasets
- Consider using local speech models for offline operation

## Security Considerations

- API keys should be stored securely in environment variables
- Implement rate limiting for API endpoints
- Validate and sanitize all user inputs
- Use HTTPS in production environments
- Implement proper authentication and authorization

## Future Enhancements

- Integration with local Whisper model for offline speech recognition
- Support for video pitch analysis
- Advanced analytics and reporting features
- Multi-language support
- Integration with external data sources
- Real-time collaboration features
- Mobile application development

## Contributing

To contribute to the VC Multi-Agent System:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add appropriate tests
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation for common solutions

---

*This documentation provides a comprehensive guide to understanding, installing, and using the VC Multi-Agent System. For technical details about specific components, refer to the inline code documentation.*

