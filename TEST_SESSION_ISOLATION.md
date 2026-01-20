# Session Isolation Testing Guide

## Changes Made

### Backend Changes:
1. **main.py**:
   - Added `session_id` field to `ChatRequest` and `VoiceChatRequest` models
   - Modified `/evaluate_pitch` to generate unique `session_id` using `uuid4()`
   - Updated pitch document storage to include `session_id` in metadata
   - Modified `/chat` endpoint to accept and propagate `session_id`
   - Updated RAG search calls to filter by `session_id`
   - Store conversation messages with `session_id` in metadata
   - Return `session_id` in all relevant responses

2. **qdrant_manager.py**:
   - Added `session_filter` parameter to `search()` method
   - Implemented Qdrant filtering using `models.Filter` with `FieldCondition`
   - Filter searches by `session_id` when provided

### Frontend Changes:
1. **App.jsx**:
   - Extract `session_id` from `/evaluate_pitch` response
   - Store `session_id` in pitchData state
   - Pass `session_id` to ConversationInterface

2. **ConversationInterface.jsx**:
   - Accept `sessionId` prop from parent
   - Track session ID in component state
   - Send `session_id` in all chat requests
   - Update session ID from backend response if not set

## How It Works

### Flow:
1. User submits pitch → `/evaluate_pitch` generates unique `session_id`
2. All pitch documents stored with `session_id` in metadata
3. Frontend receives and stores `session_id`
4. Every chat message includes `session_id` in request
5. Backend filters RAG searches to only return documents with matching `session_id`
6. Conversation messages stored with `session_id` for future retrieval

### Data Isolation:
- **Pitch A (session_id: abc-123)**: Documents tagged with "abc-123"
- **Pitch B (session_id: xyz-789)**: Documents tagged with "xyz-789"
- When searching for Pitch A context, only documents with "abc-123" are returned
- When searching for Pitch B context, only documents with "xyz-789" are returned

## Testing Steps

### Test 1: Single Pitch
1. Submit a pitch with company name "TechCo"
2. Note the session_id in browser console
3. Have a conversation about TechCo
4. Verify all responses are relevant to TechCo

### Test 2: Multiple Pitches (Isolation Test)
1. Submit Pitch 1: "AI Startup" with details about AI/ML
2. Complete a brief conversation
3. Go back and submit Pitch 2: "FinTech Startup" with details about finance
4. Start conversation about FinTech
5. **Expected**: Agent should NOT reference AI/ML from Pitch 1
6. **Expected**: Agent should only use FinTech context from Pitch 2

### Test 3: Session Persistence
1. Submit a pitch and start conversation
2. Note the session_id
3. Refresh page (if session storage implemented)
4. Continue conversation
5. **Expected**: Context should remain consistent within same session

## Verification

### Check Backend Logs:
```
Found X results for query: '...' (session: abc-123) from ...
```

### Check Qdrant Storage:
Each document should have metadata:
```json
{
  "content": "...",
  "session_id": "abc-123",
  "type": "pitch_document",
  "company_name": "..."
}
```

### Check Network Requests:
Chat requests should include:
```json
{
  "message": "...",
  "history": [...],
  "pitch_context": {...},
  "session_id": "abc-123"
}
```

## Expected Behavior

✅ Each pitch gets unique session ID
✅ RAG searches only return documents from same session
✅ Conversation history isolated per session
✅ No context leakage between different pitches
✅ Session ID persists throughout conversation

## Notes

- Session IDs are UUIDs (e.g., "f47ac10b-58cc-4372-a567-0e02b2c3d479")
- Frontend maintains session state during conversation
- Backend never mixes data from different sessions
- Old pitch data remains in Qdrant but won't interfere with new pitches
