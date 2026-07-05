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

# Chroma Configuration
CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_storage'))
CHROMA_COLLECTION = os.getenv('CHROMA_COLLECTION', 'vc_pitches')

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

# Validate critical configuration
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to your .env file.")
