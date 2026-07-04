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

# Qdrant Configuration
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'vc_pitches')

# Voice Processing Configuration
SPEECH_RECOGNITION_LANGUAGE = os.getenv('SPEECH_RECOGNITION_LANGUAGE', 'en-US')

# Server Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))

# Validate critical configuration
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to your .env file.")
