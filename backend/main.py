# main.py
from fastapi import FastAPI, HTTPException, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel
from rag_services import get_rag_service
from session_services import get_session_service
from auth_service import AuthService, UserCreate, UserLogin  # Add this
from config import get_settings  # Add this
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()  # Add this line
app = FastAPI(title="RAG Chatbot API", version="1.0.0")

#local_temporary_store
dummy_user_id = "0"
dummy_session_id = "0"



# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserPrompt(BaseModel):
    prompt: str 
    session_id: str

class CreateSessionRequest(BaseModel):
    user_id: str

# Initialize service on startup
@app.on_event("startup")
async def startup_event():
    try:
        # This will initialize the RAG service
        get_rag_service()
        # This will initialize the Session service
        get_session_service()
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "RAG Chatbot API", "status": "healthy"}

@app.post("/api/chat/prompt")
async def make_prompt(request: UserPrompt):
    try:
        print("What is wrong here")
        rag_service = get_rag_service()
        session_service = get_session_service()
        session_service.add_message(request.session_id, "user", request.prompt)
        
        raw_messages = session_service.get_session_messages(request.session_id)
        langchain_messages = []
        for msg in raw_messages:
            if msg["type"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                langchain_messages.append(AIMessage(content=msg["content"]))
        response = rag_service.get_response(request.prompt, langchain_messages)
        session_service.add_message(request.session_id, "ai", response["answer"])
        # print("Messages in the database:", session_service.get_session_messages(dummy_session_id))
       
        return {
            "userPrompt": request.prompt,
            "llm_response": response["answer"]
        }
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")

@app.get("/api/chat/messages/{session_id}")
async def get_session_messages(session_id: str, limit: int = 50):
    """Get messages for a session with optional limit"""
    try:
        session_service = get_session_service()
        messages = session_service.get_session_messages(session_id, limit)
        
        # Convert LangChain messages back to JSON format for frontend
        message_data = [
            {   
                "id": msg["message_id"],
                "type": msg["type"],
                "content": msg["content"]
            }
            for msg in messages
        ]
        
        print("Returning the following message_data: ", message_data)
        return {
            "session_id": session_id,
            "messages": message_data,
            "count": len(message_data)
        }
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/sessions")
async def get_user_sessions(user_id: str, limit: int = 10):
    """Get all chat sessions for a user"""
    print("Did I even make it here?")
    try:
        session_service = get_session_service()
        sessions = session_service.get_user_sessions(user_id, limit)
        
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions")
async def create_new_session(request: CreateSessionRequest):
    """Create new session - smart logic for anonymous vs registered users"""
    try:
        session_service = get_session_service()
        session_id = session_service.create_session_smart(request.user_id)
        
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    try:
        session_service = get_session_service()
        session_service.delete_session(session_id)
        return {"message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}


## AUTHENTICATION SERVICES ##

# Initialize auth service
def get_auth_service():
    session_service = get_session_service()
    return AuthService(session_service, session_service.users)

@app.post("/api/auth/register")
async def register(user_data: UserCreate, response: Response, anonymous_user_id: str = None):
    try:
        auth_service = get_auth_service()
        result = auth_service.register_user(user_data, anonymous_user_id)
        
        # Set JWT in httpOnly cookie
        response.set_cookie(
            key="auth_token",
            value=result["token"],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
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
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(login_data: UserLogin, response: Response):
    try:
        auth_service = get_auth_service()
        result = auth_service.login_user(login_data)
        
        # Set JWT in httpOnly cookie
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

@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_current_user(auth_token: str = Cookie(None)):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    auth_service = get_auth_service()
    payload = auth_service.verify_token(auth_token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = auth_service.users.find_one({"user_id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "user_type": "registered"
    }