# main.py
from fastapi import FastAPI, HTTPException, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel
from rag_services import get_rag_service
from session_services import get_session_service
from auth_service import AuthService, UserCreate, UserLogin
from config import get_settings
import logging
import uvicorn

# Configure application logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration settings
settings = get_settings()

# Initialize FastAPI application
app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# Legacy dummy variables - consider removing if no longer needed
dummy_user_id = "0"
dummy_session_id = "0"

# CORS middleware - enables frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,    # Allowed frontend domains
    allow_credentials=True,                 # Enable cookies/auth headers
    allow_methods=["*"],                    # Allow all HTTP methods
    allow_headers=["*"],                    # Allow all request headers
)

# Pydantic models for request validation

# Request model for chat prompts
class UserPrompt(BaseModel):
    prompt: str         # User's message/question
    session_id: str     # Chat session identifier

# Request model for creating new chat sessions
class CreateSessionRequest(BaseModel):
    user_id: str        # User identifier (registered or anonymous)

# Application startup - initialize all services
@app.on_event("startup")
async def startup_event():
    try:
        # Initialize RAG (Retrieval-Augmented Generation) service
        get_rag_service()
        # Initialize session management service
        get_session_service()
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {e}")
        raise

# Basic health check endpoint
@app.get("/")
async def root():
    return {"message": "RAG Chatbot API", "status": "healthy"}

# Main chat endpoint - processes user messages and returns AI responses
@app.post("/api/chat/prompt")
async def make_prompt(request: UserPrompt):
    try:
        rag_service = get_rag_service()
        session_service = get_session_service()
        
        # Store user message in session history
        session_service.add_message(request.session_id, "user", request.prompt)
        
        # Convert session history to LangChain message format
        raw_messages = session_service.get_session_messages(request.session_id)
        langchain_messages = []
        for msg in raw_messages:
            if msg["type"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                langchain_messages.append(AIMessage(content=msg["content"]))
        
        # Get AI response using RAG (context + conversation history)
        response = rag_service.get_response(request.prompt, langchain_messages)
        
        # Store AI response in session history
        session_service.add_message(request.session_id, "ai", response["answer"])
       
        return {
            "userPrompt": request.prompt,
            "llm_response": response["answer"]
        }
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")

# Get chat history for a specific session
@app.get("/api/chat/messages/{session_id}")
async def get_session_messages(session_id: str, limit: int = 50):
    """Get messages for a session with optional limit"""
    try:
        session_service = get_session_service()
        messages = session_service.get_session_messages(session_id, limit)
        
        # Convert database format to frontend-expected format
        message_data = [
            {   
                "id": msg["message_id"],
                "type": msg["type"],
                "content": msg["content"]
            }
            for msg in messages
        ]
        
        return {
            "session_id": session_id,
            "messages": message_data,
            "count": len(message_data)
        }
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get all chat sessions for a user (for sidebar display)
@app.get("/api/users/{user_id}/sessions")
async def get_user_sessions(user_id: str, limit: int = 10):
    """Get all chat sessions for a user"""
    try:
        session_service = get_session_service()
        sessions = session_service.get_user_sessions(user_id, limit)
        
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create new chat session with smart logic for user types
@app.post("/api/sessions")
async def create_new_session(request: CreateSessionRequest):
    """Create new session - smart logic for anonymous vs registered users"""
    try:
        session_service = get_session_service()
        # Smart logic handles different behavior for anonymous vs registered users
        session_id = session_service.create_session_smart(request.user_id)
        
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete a chat session
@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    try:
        session_service = get_session_service()
        session_service.delete_session(session_id)
        return {"message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Application health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}


## AUTHENTICATION SERVICES ##

# Factory function to create auth service with dependencies
def get_auth_service():
    session_service = get_session_service()
    return AuthService(session_service, session_service.users)

# User registration endpoint with optional anonymous user linking
@app.post("/api/auth/register")
async def register(user_data: UserCreate, response: Response, anonymous_user_id: str = None):
    try:
        auth_service = get_auth_service()
        # Register user and optionally link existing anonymous sessions
        result = auth_service.register_user(user_data, anonymous_user_id)
        
        # Set JWT token in secure HTTP-only cookie
        response.set_cookie(
            key="auth_token",
            value=result["token"],
            httponly=True,                                      # Prevents XSS attacks
            secure=False,                                       # Set to True in production with HTTPS
            samesite="lax",                                     # CSRF protection
            max_age=settings.jwt_expiration_hours * 3600        # Cookie expiration
        )
        
        # Return user data (without sensitive token)
        return {
            "user_id": result["user_id"],
            "email": result["email"],
            "name": result["name"],
            "user_type": result["user_type"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# User login endpoint
@app.post("/api/auth/login")
async def login(login_data: UserLogin, response: Response):
    try:
        auth_service = get_auth_service()
        result = auth_service.login_user(login_data)
        
        # Set JWT token in secure HTTP-only cookie
        response.set_cookie(
            key="auth_token",
            value=result["token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.jwt_expiration_hours * 3600
        )
        
        return {
            "user_id": result["user_id"],
            "email": result["email"],
            "name": result["name"],
            "user_type": result["user_type"]
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

# User logout endpoint
@app.post("/api/auth/logout")
async def logout(response: Response):
    # Clear authentication cookie
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}

# Get current authenticated user info
@app.get("/api/auth/me")
async def get_current_user(auth_token: str = Cookie(None)):
    # Check if auth token exists in cookies
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    auth_service = get_auth_service()
    # Verify and decode JWT token
    payload = auth_service.verify_token(auth_token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Fetch user data from database
    user = auth_service.users.find_one({"user_id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "user_type": "registered"
    }

# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app", 
#         host="0.0.0.0", 
#         port=8000, 
#         reload=True  # For development
#     )