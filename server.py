from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
import uuid
from fastapi.security import APIKeyHeader

# Import agent_executor and MEMORY_KEY from agent_logic.py
from agent_logic import agent_executor, MEMORY_KEY
# Import chat history manager
from chat_history import chat_history_manager

app = FastAPI(title="AI Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use header for session identification
X_SESSION_ID = APIKeyHeader(name="X-Session-ID", auto_error=False)

async def get_session_id(x_session_id: str = Depends(X_SESSION_ID)):
    """Get or create a session ID for the chat"""
    if not x_session_id:
        # Generate a new session ID if none provided
        return str(uuid.uuid4())
    return x_session_id

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    additional_data: Optional[Dict] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session_id: str = Depends(get_session_id)):
    try:
        # Add user message to chat history
        chat_history_manager.add_message(session_id, "user", request.message)
        
        # Get chat history in LangChain format
        langchain_chat_history = chat_history_manager.get_langchain_history(session_id)
        
        # Invoke agent executor with input and chat history
        result = agent_executor.invoke({
            "input": request.message,
            MEMORY_KEY: langchain_chat_history
        })
        
        agent_response = result.get("output", "Sorry, I didn't get a clear response.")
        
        # Add assistant response to chat history
        chat_history_manager.add_message(session_id, "assistant", agent_response)
        
        return ChatResponse(
            session_id=session_id,
            response=agent_response,
            additional_data=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a specific session"""
    chat_history_manager.clear_history(session_id)
    return {"status": "success", "message": f"Chat history cleared for session {session_id}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 