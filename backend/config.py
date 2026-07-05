import os
from dotenv import load_dotenv

# Load environment variables from .env file in root folder
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Gemini (Gemma) Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# Legacy OpenRouter/Mistral Configuration (kept for backward compatibility)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
MISTRAL_MODEL = os.getenv('MISTRAL_MODEL', 'mistralai/mistral-7b-instruct-v0.1')

# Pinecone Configuration (vector store - hosted, so it survives deployment
# to platforms with ephemeral/stateless filesystems, unlike embedded Chroma)
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', '')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'vc-pitches')
PINECONE_CLOUD = os.getenv('PINECONE_CLOUD', 'aws')
PINECONE_REGION = os.getenv('PINECONE_REGION', 'us-east-1')

# Tavily Configuration (market research web search)
# Free tier: 1,000 credits/month, no credit card - https://tavily.com
# Falls back to Tavily's rate-limited keyless mode if unset.
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')

# Voice Processing Configuration
SPEECH_RECOGNITION_LANGUAGE = os.getenv('SPEECH_RECOGNITION_LANGUAGE', 'en-US')

# Server Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))

# Admin Panel Configuration
# Leaving this unset disables /admin/login entirely (always rejects).
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

# Self-Ping / Keep-Alive Configuration
# IMPORTANT: for this to actually stop a host like Render/Railway from
# spinning the app down on free tiers, SELF_PING_URL must be the app's
# PUBLIC deployed URL (e.g. https://your-app.onrender.com/health), not
# localhost. Those platforms detect idleness from external traffic
# hitting their edge/proxy - a loopback request from inside the same
# process never reaches that edge, so it won't reset their idle timer.
# localhost is only useful here for local testing that the pinger works.
SELF_PING_URL = os.getenv('SELF_PING_URL', f'http://localhost:{PORT}/health')
SELF_PING_INTERVAL_MINUTES = int(os.getenv('SELF_PING_INTERVAL_MINUTES', '13'))
SELF_PING_ENABLED = os.getenv('SELF_PING_ENABLED', 'True').lower() == 'true'

# Validate critical configuration
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to your .env file.")
