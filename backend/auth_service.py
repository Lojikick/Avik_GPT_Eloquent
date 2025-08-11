from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import uuid
from config import get_settings

# Load application settings and initialize password hashing context
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Secure password hashing with bcrypt

# Pydantic models for request validation

# User registration data model
class UserCreate(BaseModel):
    email: str      # User's email address (used as login identifier)
    password: str   # Plain text password (will be hashed before storage)
    name: str       # User's display name

# User login data model
class UserLogin(BaseModel):
    email: str      # Email for login
    password: str   # Password for authentication

class AuthService:
    """
    Handles all authentication operations including:
    - User registration and login
    - Password hashing and verification
    - JWT token creation and validation
    - Anonymous user session migration
    """
    
    def __init__(self, session_service, user_collection):
        self.session_service = session_service    # Reference to session management service
        self.users = user_collection             # MongoDB collection for user data
    
    # Password security methods
    def hash_password(self, password: str) -> str:
        """Convert plain text password to secure bcrypt hash"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify plain text password against stored hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    # JWT token management
    def create_jwt_token(self, user_id: str, email: str) -> str:
        """Create signed JWT token with user info and expiration"""
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        payload = {
            "user_id": user_id,                     # User identifier
            "email": email,                         # User email
            "exp": expire,                          # Token expiration time
            "iat": datetime.utcnow()               # Token issued at time
        }
        # Sign token with secret key
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Decode and verify JWT token, return payload or None if invalid"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None  # Token is invalid, expired, or malformed
    
    # User registration workflow
    def register_user(self, user_data: UserCreate, anonymous_user_id: str = None) -> dict:
        """Register new user with optional anonymous session migration"""
        
        # Check for duplicate email addresses
        if self.users.find_one({"email": user_data.email}):
            raise ValueError("Email already registered")
        
        # Create new user document
        user_id = str(uuid.uuid4())  # Generate unique user ID
        user_doc = {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": self.hash_password(user_data.password),  # Store hashed password only
            "user_type": "registered",
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        
        # Save user to database
        self.users.insert_one(user_doc)
        
        # Transfer anonymous sessions to new registered account
        if anonymous_user_id:
            self.migrate_anonymous_sessions(anonymous_user_id, user_id)
        
        # Create authentication token for immediate login
        token = self.create_jwt_token(user_id, user_data.email)
        
        return {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "token": token,
            "user_type": "registered"
        }
    
    # User login workflow
    def login_user(self, login_data: UserLogin) -> dict:
        """Authenticate user and return user data with JWT token"""
        
        # Find user by email and verify password
        user = self.users.find_one({"email": login_data.email})
        if not user or not self.verify_password(login_data.password, user["password_hash"]):
            raise ValueError("Invalid email or password")
        
        # Update user's last active timestamp
        self.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"last_active": datetime.utcnow()}}
        )
        
        # Create new authentication token
        token = self.create_jwt_token(user["user_id"], user["email"])
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "token": token,
            "user_type": "registered"
        }
    
    # Anonymous to registered user migration
    def migrate_anonymous_sessions(self, anonymous_user_id: str, new_user_id: str):
        """Transfer anonymous user's chat sessions to newly registered user account"""
        
        # Update all sessions owned by anonymous user to new registered user
        result = self.session_service.sessions.update_many(
            {"user_id": anonymous_user_id},              # Find sessions with anonymous ID
            {"$set": {"user_id": new_user_id}}          # Update to registered user ID
        )
        
        print(f"Migrated {result.modified_count} sessions from {anonymous_user_id} to {new_user_id}")
        
        # This preserves chat history when users create accounts, 
        # providing seamless transition from guest to registered user