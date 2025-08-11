from functools import lru_cache
from pymongo import MongoClient
from datetime import datetime
from config import get_settings
import uuid
import os

class ChatSessionService:
    """
    MongoDB-based session management service
    
    Manages three collections:
    - users: User account information
    - sessions: Chat session metadata 
    - messages: Individual chat messages
    
    Handles different logic for anonymous vs registered users
    """
    
    def __init__(self):
        settings = get_settings()
        
        # Initialize MongoDB client with write safety settings
        self.client = MongoClient(
            settings.mongodb_uri, 
            w=1,    # Write concern: wait for acknowledgment from primary node
            j=True  # Journal: wait for write to be committed to journal (durability)
        )
        self.db = self.client.chatbot_db
        
        # Three main collections for the chatbot data model
        self.users = self.db.users        # User accounts and profiles
        self.sessions = self.db.sessions  # Chat session metadata
        self.messages = self.db.messages  # Individual chat messages
        
        # Create database indexes for optimal query performance
        self._create_indexes()
    
    # USER OPERATIONS
    
    def create_user(self, email: str, name: str) -> str:
        """Create new user account and return user ID"""
        user_id = str(uuid.uuid4())  # Generate unique identifier
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
        """Retrieve user document by ID"""
        return self.users.find_one({"user_id": user_id})
    
    # SESSION OPERATIONS
    
    def create_session(self, user_id: str) -> str:
        """Create new chat session for any user type"""
        session_id = str(uuid.uuid4())
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "title": "New Chat",                    # Default title, updated with first message
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0,                     # Track number of messages for UI
            "is_active": True                       # Soft delete flag
        }
        self.sessions.insert_one(session_doc)
        return session_id
    
    def get_user_sessions(self, user_id: str, limit: int = 20):
        """Get chat sessions with different logic for anonymous vs registered users"""
        
        if user_id.startswith("anon_"):
            # Anonymous users: Only show their single active session
            # This prevents sidebar clutter for guest users
            cursor = self.sessions.find({
                "user_id": user_id, 
                "is_active": True
            }).limit(1)  # Limit to one session for anonymous users
        else:
            # Registered users: Show all active sessions, newest first
            cursor = self.sessions.find({
                "user_id": user_id, 
                "is_active": True
            }).sort("updated_at", -1).limit(limit)  # Most recent sessions first
        
        # Convert MongoDB documents to frontend-friendly format
        sessions = []
        for doc in cursor:
            sessions.append({
                "session_id": doc["session_id"],
                "title": doc.get("title", "New Chat"),
                "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
                "message_count": doc.get("message_count", 0),
            })
        
        return sessions
        
    # MESSAGE OPERATIONS
    
    def add_message(self, session_id: str, message_type: str, content: str):
        """Add message to session and update session metadata"""
        message_id = str(uuid.uuid4())
        message_doc = {
            "message_id": message_id,
            "session_id": session_id,
            "type": message_type,       # "user" or "ai"
            "content": content,
            "timestamp": datetime.utcnow()
        }
        
        # Insert the message
        self.messages.insert_one(message_doc)
        
        # Update session metadata atomically
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"updated_at": datetime.utcnow()},    # Update last activity
                "$inc": {"message_count": 1}                  # Increment message counter
            }
        )
        
        return message_id
    
    def get_session_messages(self, session_id: str, limit: int = 50):
        """Retrieve messages for a session in chronological order"""
        return list(self.messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).limit(limit))  # Oldest first for conversation flow
    
    def _create_indexes(self):
        """Create database indexes for query optimization"""
        
        # Composite index for user session queries (user_id + sort by updated_at)
        self.sessions.create_index([("user_id", 1), ("updated_at", -1)])
        
        # Composite index for session message queries (session_id + sort by timestamp)
        self.messages.create_index([("session_id", 1), ("timestamp", 1)])
        
        # Unique index for fast session lookups
        self.sessions.create_index("session_id")

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session and all associated messages (cascade delete)
        Returns True if successful, False if session not found
        """
        try:
            # First, delete all messages in this session
            messages_result = self.messages.delete_many({"session_id": session_id})
            
            # Then, delete the session document
            session_result = self.sessions.delete_one({"session_id": session_id})
            
            if session_result.deleted_count > 0:
                return True
            else:
                return False
                
        except Exception as e:
            return False

    # ANONYMOUS USER SPECIFIC OPERATIONS
    
    def get_or_create_anonymous_session(self, user_id: str) -> str:
        """
        For anonymous users: Get existing session or create new one
        Ensures only one active session per anonymous user ID
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
        Clear existing messages but reuse the same session
        This prevents anonymous users from accumulating multiple sessions
        """
        # Find the user's active session
        existing_session = self.sessions.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if existing_session:
            session_id = existing_session["session_id"]
            
            # Delete all messages in this session (fresh start)
            self.messages.delete_many({"session_id": session_id})
            
            # Reset session metadata to default state
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
        Intelligent session creation based on user type
        
        Anonymous users: Reuse/reset existing session (prevents clutter)
        Registered users: Create new session normally (preserves history)
        """
        if user_id.startswith("anon_"):
            # Anonymous users get their session content replaced
            return self.replace_anonymous_session_content(user_id)
        else:
            # Registered users get a brand new session
            return self.create_session(user_id)

# Singleton pattern - ensures one service instance across the application
@lru_cache()
def get_session_service():
    """
    Factory function that returns cached session service instance
    
    Benefits:
    - Reuses MongoDB connection across requests
    - Prevents multiple database connection overhead
    - Ensures consistent service state
    """
    return ChatSessionService()