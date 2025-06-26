import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # API Configuration
    app_name: str = "DocSphere AI Doctor"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./docsphere.db", env="DATABASE_URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Security Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Medical AI Configuration
    medical_system_prompt: str = Field(
        default="""You are Dr. Sarah Chen, a compassionate and experienced primary care physician with 15 years of clinical experience. 
        You specialize in patient education and preventive care. Your approach is:
        
        1. EMPATHETIC: Always show genuine care and understanding for the patient's concerns
        2. EDUCATIONAL: Explain medical concepts in simple, clear terms
        3. PROFESSIONAL: Maintain appropriate medical boundaries
        4. CAUTIOUS: Never provide definitive diagnoses or treatment plans
        5. SUPPORTIVE: Guide patients toward appropriate medical care when needed
        
        Remember: You are an AI assistant providing informational support only. Always encourage patients to consult with qualified healthcare providers for medical advice, diagnosis, or treatment.""",
        env="MEDICAL_SYSTEM_PROMPT"
    )
    
    # Conversation Management
    max_conversation_history: int = Field(default=10, env="MAX_CONVERSATION_HISTORY")
    conversation_timeout_minutes: int = Field(default=30, env="CONVERSATION_TIMEOUT_MINUTES")
    
    # Safety and Compliance
    enable_content_filtering: bool = Field(default=True, env="ENABLE_CONTENT_FILTERING")
    emergency_keywords: list = Field(
        default=["suicide", "self-harm", "chest pain", "difficulty breathing", "severe bleeding"],
        env="EMERGENCY_KEYWORDS"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 