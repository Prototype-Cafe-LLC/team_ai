"""Configuration settings for the multi-agent system."""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Multi-Agent Development System"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database
    postgres_url: str = "postgresql://postgres:postgres@postgres:5432/multiagent"
    redis_url: str = "redis://redis:6379"
    
    # LLM APIs
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # LLM Settings
    llm_model: str = "claude-3-sonnet-20240229"  # Using Claude 3 Sonnet
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000
    
    # Agent Settings
    max_review_iterations: int = 3
    agent_timeout: int = 300  # seconds
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost"
    
    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_message_queue_size: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()