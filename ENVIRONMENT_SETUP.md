# Environment Setup Guide

## Overview
This project uses environment variables stored in a `.env` file to manage sensitive configuration like API keys. The `.env` file is **NOT** committed to Git for security.

## Setup Instructions

### Step 1: Copy the Example File
```bash
# From the project root
cp .env.example .env
```

### Step 2: Get Your API Keys

#### OpenRouter API Key (Required)
1. Go to https://openrouter.ai/
2. Sign up or log in
3. Navigate to Settings → Keys
4. Create a new API key
5. Copy the key and paste it in `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

#### Qdrant Database (Choose One)

**Option A: Local Qdrant (Free, for development)**
```bash
# Install Docker if you haven't already
# Then run Qdrant in a Docker container:
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant

# Your .env will be:
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
```

**Option B: Qdrant Cloud (Recommended for production)**
1. Sign up at https://qdrant.tech/
2. Create a new cloud cluster
3. Copy your cluster URL and API key
4. Update `.env`:
```
QDRANT_URL=https://your-instance-id.region.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key-here
```

### Step 3: Verify Configuration
```bash
# From backend folder
cd backend
python config.py  # This will validate your .env file
```

## .env File Structure

```env
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-actual-key

# Qdrant Configuration  
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Optional Server Config
DEBUG=False
HOST=0.0.0.0
PORT=8000
```

## File Locations

- **Root folder**: Place your `.env` file here
  ```
  vc_multi_agent_system/
  ├── .env          ← Your actual keys (NEVER COMMIT)
  ├── .env.example  ← Template (commit this)
  ├── backend/
  ├── frontend/
  └── ...
  ```

## Security Best Practices

### ✅ DO:
- Keep `.env` in the root folder only
- Use strong, unique API keys
- Rotate API keys regularly
- Store `.env` securely (use password manager for backup)
- Add `.env` to `.gitignore` (already done)

### ❌ DON'T:
- Commit `.env` to Git
- Share `.env` file via email or chat
- Use the same key across multiple projects
- Hardcode API keys in source code
- Push `.env` to public repositories

## Troubleshooting

### "OPENROUTER_API_KEY is not set"
- Make sure `.env` file exists in the root folder
- Verify you've filled in `OPENROUTER_API_KEY=...`
- Check for typos in the variable name

### "Could not connect to Qdrant"
- If using local Docker: ensure container is running
  ```bash
  docker ps | grep qdrant
  docker start qdrant  # If stopped
  ```
- If using cloud: verify URL and API key
- Check your internet connection

### Backend won't start
- Ensure all required environment variables are set
- Run: `python -c "from config import *"` to debug

## Running with Environment Variables

### Backend
```bash
cd backend
pip install python-dotenv
python -m uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
pnpm dev
```

## Deployment Notes

For production deployment:
1. Never include `.env` in Docker images
2. Use deployment platform's secrets management (AWS Secrets Manager, Vercel Env Vars, etc.)
3. Set environment variables in your hosting platform
4. Example for Vercel:
   - Go to Project Settings → Environment Variables
   - Add: `OPENROUTER_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`

## Support

If you have issues:
1. Check the `.env.example` file for required variables
2. Ensure all API keys are valid and active
3. Review the troubleshooting section above
4. Check backend logs: `tail -f logs/*.log`
