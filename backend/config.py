# config.py
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

# Configuration class using Pydantic for type validation and environment variable loading
class Settings(BaseSettings):
    
    # Environment and CORS configuration
    environment: str = "development"                    # Current deployment environment
    allowed_origins: list = ["http://localhost:3000"]  # Basic CORS origins list (consider using cors_origins property instead)

    # External API keys - loaded from environment variables
    google_api_key: str         # For Google Gemini LLM API access
    pinecone_api_key: str       # For Pinecone vector database operations
    mongodb_uri: str            # MongoDB connection string for user/session data
    
    # Pinecone vector database configuration
    pinecone_environment: str = "us-east-1-aws"                    # Pinecone cloud region
    pinecone_index_name: str = "ai-powered-chatbot-challenge"      # Vector index name for embeddings
    
    # AI model configuration
    embedding_model: str = "llama-text-embed-v2"     # Model for converting text to vectors
    llm_model: str = "gemini-1.5-flash"              # Large language model for chat responses
    llm_temperature: float = 0.7                     # Controls randomness in AI responses (0.0 = deterministic, 1.0 = creative)
    
    # JWT authentication configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"  # Key for signing JWT tokens
    jwt_algorithm: str = "HS256"                      # JWT signing algorithm
    jwt_expiration_hours: int = 24 * 7                # Token validity period (7 days)

    
    # Dynamic CORS origins based on environment
    @property
    def cors_origins(self):
        if self.environment == "production":
            return ["https://my-domain.com"]  # Production domain whitelist, which would be used for an actual production environment hosted on AWS
        return ["http://localhost:3000", "http://127.0.0.1:3000"]  # Development domains
    
    # Pydantic configuration
    class Config:
        env_file = ".env"  # Automatically load environment variables from .env file

# Cached settings instance - prevents re-reading .env file on every import
@lru_cache()
def get_settings():
    return Settings()