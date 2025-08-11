from functools import lru_cache
from pymongo import MongoClient
from datetime import datetime
from config import get_settings
import uuid
import os

class ChatSessionService:
    def __init__(self):
        settings = get_settings()
        self.client = MongoClient(settings.mongodb_uri)
        self.db = self.client.chatbot_db
        
        # Your three collections
        self.users = self.db.users
        self.sessions = self.db.sessions  
        self.messages = self.db.messages
        
        self._create_indexes()
    
    # User operations
    def create_user(self, email: str, name: str) -> str:
        user_id = str(uuid.uuid4())
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        self.users.insert_one(user_doc)
        return user_id
    
    def get_user(self, user_id: str):
        return self.users.find_one({"user_id": user_id})
    
    # Session operations
    def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "title": "New Chat",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0,
            "is_active": True
        }
        self.sessions.insert_one(session_doc)
        return session_id
    
    def get_user_sessions(self, user_id: str, limit: int = 20):
        """Get sessions with anonymous user logic"""
        
        if user_id.startswith("anon_"):
            # For anonymous users: return only their single active session
            cursor = self.sessions.find({
                "user_id": user_id, 
                "is_active": True
            }).limit(1)  # Only one session for anonymous users
        else:
            # For registered users: return all active sessions
            cursor = self.sessions.find({
                "user_id": user_id, 
                "is_active": True
            }).sort("updated_at", -1).limit(limit)
        
        sessions = []
        for doc in cursor:
            sessions.append({
                "session_id": doc["session_id"],
                "title": doc.get("title", "New Chat"),
                "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
                "message_count": doc.get("message_count", 0),
            })
        
        return sessions
        
    # Message operations
    def add_message(self, session_id: str, message_type: str, content: str):
        message_id = str(uuid.uuid4())
        message_doc = {
            "message_id": message_id,
            "session_id": session_id,
            "type": message_type,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        
        # Insert message
        self.messages.insert_one(message_doc)
        
        # Update session metadata
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"updated_at": datetime.utcnow()},
                "$inc": {"message_count": 1}
            }
        )
        
        return message_id
    
    def get_session_messages(self, session_id: str, limit: int = 50):
        return list(self.messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).limit(limit))
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        # Index for finding user's sessions
        self.sessions.create_index([("user_id", 1), ("updated_at", -1)])
        
        # Index for finding session messages
        self.messages.create_index([("session_id", 1), ("timestamp", 1)])
        
        # Index for session lookup
        self.sessions.create_index("session_id")

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its associated messages
        Returns True if session was found and deleted, False otherwise
        """
        try:
            # First, delete all messages associated with this session
            messages_result = self.messages.delete_many({"session_id": session_id})
            
            # Then, delete the session itself
            session_result = self.sessions.delete_one({"session_id": session_id})
            
            if session_result.deleted_count > 0:
                print(f"Deleted session {session_id} and {messages_result.deleted_count} associated messages")
                return True
            else:
                print(f"Session {session_id} not found")
                return False
                
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
        


    def get_or_create_anonymous_session(self, user_id: str) -> str:
        """
        For anonymous users: Get existing session or create new one
        Ensures only one active session per anonymous user
        """
        # Check if anonymous user already has an active session
        existing_session = self.sessions.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if existing_session:
            return existing_session["session_id"]
        else:
            # Create new session for first-time anonymous user
            return self.create_session(user_id)

    def replace_anonymous_session_content(self, user_id: str) -> str:
        """
        For anonymous users starting a new chat:
        Clear existing messages but keep the session
        """
        # Find the user's active session
        existing_session = self.sessions.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if existing_session:
            session_id = existing_session["session_id"]
            
            # Delete all messages in this session
            self.messages.delete_many({"session_id": session_id})
            
            # Reset session metadata
            self.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "title": "New Chat",
                        "updated_at": datetime.utcnow(),
                        "message_count": 0
                    }
                }
            )
            
            return session_id
        else:
            # No existing session, create new one
            return self.create_session(user_id)

    def create_session_smart(self, user_id: str) -> str:
        """
        Smart session creation based on user type
        """
        if user_id.startswith("anon_"):
            # For anonymous users: replace existing session content
            return self.replace_anonymous_session_content(user_id)
        else:
            # For registered users: create new session normally
            return self.create_session(user_id)
    

@lru_cache()
def get_session_service():
    """Singleton pattern for Session service"""
    return ChatSessionService()