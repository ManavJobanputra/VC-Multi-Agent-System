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

# Frontend base URL - used to build the magic-link login URL that gets
# emailed to users (points at /auth/callback on the deployed frontend).
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

# Email (magic-link login) Configuration
# Tries SMTP first if SMTP_HOST is set, then Resend if RESEND_API_KEY is
# set, then falls back to logging the link to the console - fine for
# local dev/testing, not for real users.
#
# SMTP works with Gmail (smtp.gmail.com, port 587, an App Password - not
# your regular password - from https://myaccount.google.com/apppasswords),
# Outlook (smtp.office365.com, port 587), or any other provider's SMTP.
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', SMTP_USERNAME)
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'

RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
RESEND_FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')

# Razorpay (credit pack payments) Configuration
# Get test-mode keys from https://dashboard.razorpay.com (Settings > API Keys).
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')

# Validate critical configuration
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to your .env file.")
