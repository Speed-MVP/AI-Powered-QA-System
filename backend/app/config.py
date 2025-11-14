from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str

    # GCP
    gcp_project_id: str
    gcp_bucket_name: str
    gcp_client_email: Optional[str] = None
    gcp_private_key: Optional[str] = None
    gcp_credentials_path: Optional[str] = None  # Deprecated: use gcp_client_email and gcp_private_key instead

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # APIs
    deepgram_api_key: str
    assemblyai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

    # Email
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from: str

    # Server
    environment: str = "development"
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:5173,https://ai-powered-qa-system.vercel.app,https://qualitidex.com,https://www.qualitidex.com,https://api.qualitidex.com"

    # Alignment removed

    # Gemini Service (Phase 3-4)
    gemini_use_hybrid: bool = False  # Default to Pro only for reliability
    gemini_force_pro: bool = True    # Always use Pro model (more reliable)

    # Cost Optimization Settings
    enable_expensive_features: bool = False  # Enable RAG, human examples, advanced sentiment analysis
    max_tokens_per_evaluation: int = 4000   # Token budget per evaluation
    token_cost_threshold: float = 0.01     # Alert if evaluation costs more than $0.01
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

