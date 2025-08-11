from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import uuid
from config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class AuthService:
    def __init__(self, session_service, user_collection):
        self.session_service = session_service
        self.users = user_collection
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_jwt_token(self, user_id: str, email: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None
    
    def register_user(self, user_data: UserCreate, anonymous_user_id: str = None) -> dict:
        # Check if email already exists
        if self.users.find_one({"email": user_data.email}):
            raise ValueError("Email already registered")
        
        # Create new user
        user_id = str(uuid.uuid4())
        user_doc = {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": self.hash_password(user_data.password),
            "user_type": "registered",
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        
        self.users.insert_one(user_doc)
        
        # Migrate anonymous sessions if provided
        if anonymous_user_id:
            self.migrate_anonymous_sessions(anonymous_user_id, user_id)
        
        # Create JWT token
        token = self.create_jwt_token(user_id, user_data.email)
        
        return {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "token": token,
            "user_type": "registered"
        }
    
    def login_user(self, login_data: UserLogin) -> dict:
        # Find user by email
        user = self.users.find_one({"email": login_data.email})
        if not user or not self.verify_password(login_data.password, user["password_hash"]):
            raise ValueError("Invalid email or password")
        
        # Update last active
        self.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"last_active": datetime.utcnow()}}
        )
        
        # Create JWT token
        token = self.create_jwt_token(user["user_id"], user["email"])
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "token": token,
            "user_type": "registered"
        }
    
    def migrate_anonymous_sessions(self, anonymous_user_id: str, new_user_id: str):
        """Transfer anonymous user's sessions to registered user"""
        # Update sessions
        self.session_service.sessions.update_many(
            {"user_id": anonymous_user_id},
            {"$set": {"user_id": new_user_id}}
        )
        print(f"Migrated sessions from {anonymous_user_id} to {new_user_id}")