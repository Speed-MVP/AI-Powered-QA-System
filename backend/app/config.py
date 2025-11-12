from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://placeholder:placeholder@localhost:5432/placeholder"

    # GCP
    gcp_project_id: str = "placeholder-project"
    gcp_bucket_name: str = "placeholder-bucket"
    gcp_client_email: Optional[str] = None
    gcp_private_key: Optional[str] = None
    gcp_credentials_path: Optional[str] = None  # Deprecated: use gcp_client_email and gcp_private_key instead

    # JWT
    jwt_secret: str = "placeholder-jwt-secret-that-is-long-enough-for-validation-but-should-be-replaced"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # APIs
    deepgram_api_key: str = "placeholder-deepgram-key"
    assemblyai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

    # Email
    smtp_host: str = "smtp.placeholder.com"
    smtp_port: int = 587
    smtp_user: str = "placeholder@placeholder.com"
    smtp_password: str = "placeholder-password"
    smtp_from: str = "placeholder@placeholder.com"
    
    # Server
    environment: str = "development"
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,https://qualitidex.com,https://www.qualitidex.com"

    # Alignment Service (Phase 2)
    enable_alignment: bool = True
    alignment_timeout_seconds: int = 120
    alignment_max_duration_seconds: int = 180  # Skip alignment for files longer than this

    # Gemini Service (Phase 3-4)
    gemini_use_hybrid: bool = False  # Default to Pro only for reliability
    gemini_force_pro: bool = True    # Always use Pro model (more reliable)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

