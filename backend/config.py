# config.py
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Add these 2 lines only:
    environment: str = "development"
    allowed_origins: list = ["http://localhost:3000"]  

    google_api_key: str
    pinecone_api_key: str
    mongodb_uri: str
    pinecone_environment: str = "us-east-1-aws"
    pinecone_index_name: str = "ai-powered-chatbot-challenge"
    embedding_model: str = "llama-text-embed-v2"
    llm_model: str = "gemini-1.5-flash"
    llm_temperature: float = 0.7
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24 * 7  # 7 days

    
    # Add this property:
    @property
    def cors_origins(self):
        if self.environment == "production":
            return ["https://my-domain.com"]  # You'll set this later when you have a domain
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()