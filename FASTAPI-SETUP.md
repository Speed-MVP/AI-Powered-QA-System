# FastAPI Backend Setup Guide
### AI-Powered Batch QA System MVP

---

## Overview

This guide covers the complete setup, structure, and implementation of the FastAPI backend for the AI QA system running on **GCP Cloud Run** with **Neon PostgreSQL** database.

**Why FastAPI:**
- Async/await support (perfect for I/O-bound operations like API calls to Deepgram, Gemini)
- Automatic API documentation (Swagger UI)
- Type hints with Pydantic models
- Fast performance (one of the fastest Python frameworks)
- Easy deployment as Docker container on Cloud Run
- Built-in security features (CORS, HTTPS)

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Installation & Setup](#2-installation--setup)
3. [Core Configuration](#3-core-configuration)
4. [Database Models](#4-database-models)
5. [API Endpoints](#5-api-endpoints)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [File Upload & Storage](#7-file-upload--storage)
8. [Background Tasks](#8-background-tasks)
9. [External API Integration](#9-external-api-integration)
10. [Error Handling](#10-error-handling)
11. [Docker & Deployment](#11-docker--deployment)
12. [Testing](#12-testing)

---

## 1. Project Structure

```
ai-qa-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Entry point, FastAPI app setup
│   ├── config.py               # Configuration & environment variables
│   ├── database.py             # Neon DB connection, session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py          # Company SQLAlchemy model
│   │   ├── user.py             # User model
│   │   ├── recording.py        # Recording model
│   │   ├── transcript.py       # Transcript model
│   │   ├── evaluation.py       # Evaluation model
│   │   ├── category_score.py   # Category scores model
│   │   ├── policy_template.py  # Policy template model
│   │   ├── evaluation_criteria.py  # Criteria model
│   │   └── policy_violation.py # Violations model
│   ├── schemas/                # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── recording.py
│   │   ├── evaluation.py
│   │   ├── policy_template.py
│   │   └── user.py
│   ├── routes/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── recordings.py       # Recording upload, list, get
│   │   ├── evaluations.py      # Evaluation results
│   │   ├── templates.py        # Policy templates CRUD
│   │   └── health.py           # Health check
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── storage.py          # GCP Cloud Storage operations
│   │   ├── deepgram.py         # Deepgram transcription
│   │   ├── assemblyai.py       # AssemblyAI diarization
│   │   ├── gemini.py           # Gemini LLM evaluation
│   │   ├── scoring.py          # Scoring rules engine
│   │   └── email.py            # Email notifications
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py             # JWT verification
│   │   └── permissions.py      # Role-based access
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Logging setup
│   │   ├── errors.py           # Custom exceptions
│   │   └── validators.py       # Input validation
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── process_recording.py # Background processing
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py
│       ├── test_recordings.py
│       └── conftest.py
├── migrations/                 # Alembic database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── .env                        # Environment variables (local)
├── .env.example               # Template
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Local development
├── pyproject.toml            # Project metadata
├── pytest.ini                # Test configuration
└── README.md
```

---

## 2. Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL client tools
- Google Cloud SDK
- Docker (for containerization)

### Step 1: Clone & Create Virtual Environment

```bash
git clone <repo-url>
cd ai-qa-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiohttp==3.9.1
requests==2.31.0
google-cloud-storage==2.10.0
openai==1.3.6
anthropic==0.7.1
email-validator==2.1.0
```

### Step 3: Create Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
```

**.env:**
```
# Database
DATABASE_URL=postgresql://user:password@ep-yellow-firefly-123456.us-east-1.postgres.vercel.app/neon_db

# GCP
GCP_PROJECT_ID=your-gcp-project-id
GCP_BUCKET_NAME=ai-qa-recordings
GCP_CREDENTIALS_PATH=/path/to/service-account-key.json

# Authentication
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# External APIs
DEEPGRAM_API_KEY=your-deepgram-key
ASSEMBLYAI_API_KEY=your-assemblyai-key
GEMINI_API_KEY=your-gemini-key
# OR
CLAUDE_API_KEY=your-claude-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompany.com

# Server
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Step 4: Set Up Database

```bash
# Run migrations
alembic upgrade head

# Create initial admin user
python -c "from app.scripts.create_admin import create_admin; create_admin()"
```

### Step 5: Run Development Server

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using docker-compose
docker-compose up
```

Visit: http://localhost:8000/docs (Swagger UI)

---

## 3. Core Configuration

**app/config.py:**
```python
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # GCP
    gcp_project_id: str
    gcp_bucket_name: str
    gcp_credentials_path: Optional[str] = None
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    # APIs
    deepgram_api_key: str
    assemblyai_api_key: str
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**app/database.py:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,  # Test connections before using
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()

# Dependency for routes
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    Base.metadata.create_all(bind=engine)
```

**app/main.py:**
```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.database import init_db
from app.routes import auth, recordings, evaluations, templates, health
import logging

# Setup logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI QA Backend",
    description="Automated call center quality assurance system",
    version="0.2.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI server...")
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI server...")

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(recordings.router, prefix="/api/recordings", tags=["recordings"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["evaluations"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])

@app.get("/")
async def root():
    return {"message": "AI QA Backend API - See /docs for Swagger UI"}
```

---

## 4. Database Models

**app/models/user.py:**
```python
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid

class UserRole(str, enum.Enum):
    admin = "admin"
    qa_manager = "qa_manager"
    reviewer = "reviewer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL if using OAuth
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.reviewer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    recordings = relationship("Recording", back_populates="uploaded_by_user")
    evaluations = relationship("Evaluation", back_populates="evaluated_by_user")
```

**app/models/recording.py:**
```python
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid

class RecordingStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Recording(Base):
    __tablename__ = "recordings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(Enum(RecordingStatus), default=RecordingStatus.queued, index=True)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="recordings")
    transcript = relationship("Transcript", uselist=False, back_populates="recording")
    evaluation = relationship("Evaluation", uselist=False, back_populates="recording")
```

**app/models/evaluation.py:**
```python
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid

class EvaluationStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    reviewed = "reviewed"

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False, unique=True, index=True)
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    evaluated_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    overall_score = Column(Integer, nullable=False)
    resolution_detected = Column(Boolean, nullable=False)
    resolution_confidence = Column(Float, nullable=False)
    llm_analysis = Column(JSON, nullable=False)
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    recording = relationship("Recording", back_populates="evaluation")
    policy_template = relationship("PolicyTemplate", back_populates="evaluations")
    evaluated_by_user = relationship("User", back_populates="evaluations")
    category_scores = relationship("CategoryScore", back_populates="evaluation", cascade="all, delete-orphan")
    policy_violations = relationship("PolicyViolation", back_populates="evaluation", cascade="all, delete-orphan")
```

---

## 5. API Endpoints

### Authentication

**app/routes/auth.py:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.jwt_expire_hours))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Verify JWT token and return current user"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "company_id": current_user.company_id
    }
```

### Recording Upload

**app/routes/recordings.py:**
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.recording import Recording, RecordingStatus
from app.routes.auth import get_current_user
from app.services.storage import StorageService
from app.tasks.process_recording import process_recording_task
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/signed-url")
async def get_signed_url(
    file_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get signed URL for direct upload to GCP Storage"""
    storage = StorageService()
    signed_url = storage.get_signed_upload_url(
        file_name=file_name,
        company_id=current_user.company_id
    )
    return {"signed_url": signed_url}

@router.post("/upload")
async def upload_recording(
    file_name: str,
    file_url: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create recording entry and trigger processing"""
    # Create recording in DB
    recording = Recording(
        company_id=current_user.company_id,
        uploaded_by_user_id=current_user.id,
        file_name=file_name,
        file_url=file_url,
        status=RecordingStatus.queued
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)
    
    # Trigger background processing
    background_tasks.add_task(process_recording_task, recording.id)
    
    logger.info(f"Recording {recording.id} queued for processing")
    
    return {
        "recording_id": recording.id,
        "status": recording.status.value,
        "message": "Processing started"
    }

@router.get("/list")
async def list_recordings(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List recordings for company"""
    query = db.query(Recording).filter(Recording.company_id == current_user.company_id)
    
    if status:
        query = query.filter(Recording.status == status)
    
    recordings = query.order_by(Recording.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "status": r.status.value,
            "duration_seconds": r.duration_seconds,
            "uploaded_at": r.uploaded_at.isoformat(),
            "processed_at": r.processed_at.isoformat() if r.processed_at else None
        }
        for r in recordings
    ]

@router.get("/{recording_id}")
async def get_recording(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific recording"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return {
        "id": recording.id,
        "file_name": recording.file_name,
        "status": recording.status.value,
        "error_message": recording.error_message,
        "duration_seconds": recording.duration_seconds,
        "uploaded_at": recording.uploaded_at.isoformat(),
        "processed_at": recording.processed_at.isoformat() if recording.processed_at else None
    }
```

---

## 6. Authentication & Authorization

**app/middleware/auth.py:**
```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.routes.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_routes = ["/docs", "/openapi.json", "/api/auth/login"]
        
        if any(request.url.path.startswith(route) for route in public_routes):
            return await call_next(request)
        
        # Verify JWT token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        return await call_next(request)
```

**app/middleware/permissions.py:**
```python
from app.models.user import User, UserRole
from sqlalchemy.orm import Session
from fastapi import HTTPException

def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    async def check_role(current_user: User):
        if current_user.role.value != required_role.value:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role

def require_company_access(company_id: str, current_user: User):
    """Check if user has access to company"""
    if current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
```

---

## 7. File Upload & Storage

**app/services/storage.py:**
```python
from google.cloud import storage
from app.config import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = storage.Client(project=settings.gcp_project_id)
        self.bucket = self.client.bucket(settings.gcp_bucket_name)
    
    def get_signed_upload_url(self, file_name: str, company_id: str, expiration_minutes: int = 15):
        """Generate signed URL for direct browser upload"""
        blob_name = f"{company_id}/{file_name}"
        blob = self.bucket.blob(blob_name)
        
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="PUT"
        )
        
        return signed_url
    
    def get_public_url(self, file_path: str):
        """Get public URL for file"""
        return f"https://storage.googleapis.com/{self.bucket.name}/{file_path}"
    
    def delete_file(self, file_path: str):
        """Delete file from storage"""
        blob = self.bucket.blob(file_path)
        blob.delete()
        logger.info(f"Deleted file: {file_path}")
```

---

## 8. Background Tasks

**app/tasks/process_recording.py:**
```python
from app.database import SessionLocal
from app.models.recording import Recording, RecordingStatus
from app.models.transcript import Transcript
from app.models.evaluation import Evaluation
from app.models.category_score import CategoryScore
from app.models.policy_violation import PolicyViolation
from app.services.deepgram import DeepgramService
from app.services.gemini import GeminiService
from app.services.scoring import ScoringService
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

async def process_recording_task(recording_id: str):
    """Background task to process recording"""
    db = SessionLocal()
    try:
        # Get recording
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return
        
        # Update status
        recording.status = RecordingStatus.processing
        db.commit()
        
        # Step 1: Transcribe
        logger.info(f"Transcribing {recording_id}...")
        deepgram = DeepgramService()
        transcript_data = await deepgram.transcribe(recording.file_url)
        
        # Save transcript
        transcript = Transcript(
            recording_id=recording_id,
            transcript_text=transcript_data["transcript"],
            diarized_segments=transcript_data["diarized_segments"],
            transcription_confidence=transcript_data["confidence"]
        )
        db.add(transcript)
        db.commit()
        
        # Step 2: Evaluate with LLM
        logger.info(f"Evaluating {recording_id}...")
        gemini = GeminiService()
        evaluation_data = await gemini.evaluate(
            transcript_text=transcript.transcript_text,
            policy_template_id=recording.evaluation.policy_template_id
        )
        
        # Step 3: Calculate scores
        scoring = ScoringService()
        final_scores = scoring.calculate_scores(evaluation_data)
        
        # Save evaluation
        evaluation = Evaluation(
            recording_id=recording_id,
            overall_score=final_scores["overall_score"],
            resolution_detected=final_scores["resolution_detected"],
            resolution_confidence=final_scores["resolution_confidence"],
            llm_analysis=evaluation_data
        )
        db.add(evaluation)
        db.commit()
        
        # Save category scores
        for category, score_data in final_scores["category_scores"].items():
            cat_score = CategoryScore(
                evaluation_id=evaluation.id,
                category_name=category,
                score=score_data["score"],
                feedback=score_data["feedback"]
            )
            db.add(cat_score)
        
        # Save violations
        for violation in final_scores.get("violations", []):
            policy_viol = PolicyViolation(
                evaluation_id=evaluation.id,
                criteria_id=violation["criteria_id"],
                violation_type=violation["type"],
                description=violation["description"],
                severity=violation["severity"]
            )
            db.add(policy_viol)
        
        db.commit()
        
        # Update recording status
        recording.status = RecordingStatus.completed
        recording.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Recording {recording_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing recording {recording_id}: {str(e)}")
        recording.status = RecordingStatus.failed
        recording.error_message = str(e)
        db.commit()
    
    finally:
        db.close()
```

---

## 9. External API Integration

**app/services/deepgram.py:**
```python
import aiohttp
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class DeepgramService:
    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self.base_url = "https://api.deepgram.com/v1/listen"
    
    async def transcribe(self, file_url: str):
        """Transcribe audio with diarization"""
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "model": "nova-3",
            "diarize": "true"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={"url": file_url},
                headers=headers,
                params=params
            ) as response:
                if response.status != 200:
                    raise Exception(f"Deepgram error: {response.status}")
                
                data = await response.json()
                
                # Extract transcript
                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                
                # Extract diarized segments
                words = data["results"]["channels"][0]["alternatives"][0]["words"]
                confidence = data["metadata"].get("confidence", 0)
                
                return {
                    "transcript": transcript,
                    "diarized_segments": words,
                    "confidence": confidence
                }
```

**app/services/gemini.py:**
```python
import anthropic
from app.config import settings
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.evaluation_criteria import EvaluationCriteria
import logging
import json

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        # Using Anthropic client as example (switch to Gemini SDK as needed)
    
    async def evaluate(self, transcript_text: str, policy_template_id: str):
        """Evaluate transcript using LLM"""
        db = SessionLocal()
        try:
            # Get evaluation criteria for template
            criteria = db.query(EvaluationCriteria).filter(
                EvaluationCriteria.policy_template_id == policy_template_id
            ).all()
            
            # Build prompt
            prompt = self._build_prompt(transcript_text, criteria)
            
            # Call LLM
            client = anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            response_text = message.content[0].text
            evaluation = json.loads(response_text)
            
            logger.info(f"LLM evaluation completed")
            return evaluation
        
        finally:
            db.close()
    
    def _build_prompt(self, transcript: str, criteria: list) -> str:
        """Build LLM prompt"""
        criteria_text = "\n".join([
            f"- {c.category_name} (Weight: {c.weight}%, Passing: {c.passing_score})\n  {c.evaluation_prompt}"
            for c in criteria
        ])
        
        return f"""
Evaluate this customer service call transcript based on the following criteria:

{criteria_text}

TRANSCRIPT:
{transcript}

Provide evaluation in JSON format:
{{
  "compliance": {{"score": 85, "feedback": "..."}},
  "empathy": {{"score": 90, "feedback": "..."}},
  "resolution": {{"score": 88, "feedback": "...", "resolved": true}}
}}
        """
```

---

## 10. Error Handling

**app/utils/errors.py:**
```python
from fastapi import HTTPException, status

class APIException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class AuthenticationError(APIException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class AuthorizationError(APIException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class NotFoundError(APIException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationError(APIException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class InternalServerError(APIException):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
```

**app/utils/logger.py:**
```python
import logging
import sys
from app.config import settings

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

---

## 11. Docker & Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Run migrations
RUN alembic upgrade head

# Expose port
EXPOSE 8080

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8080"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/ai_qa
      ENVIRONMENT: development
    depends_on:
      - db
    volumes:
      - .:/app

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ai_qa
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Deployment to Cloud Run:**
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/api:latest

# Deploy
gcloud run deploy api \
  --image gcr.io/PROJECT_ID/api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,GCP_PROJECT_ID=$GCP_PROJECT_ID,etc
```

---

## 12. Testing

**tests/conftest.py:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_token():
    # Generate test JWT token
    from app.routes.auth import create_access_token
    return create_access_token(data={"sub": "test-user-id"})
```

**tests/test_recordings.py:**
```python
from fastapi.testclient import TestClient

def test_upload_recording(client, sample_token):
    response = client.post(
        "/api/recordings/upload",
        json={
            "file_name": "test.mp3",
            "file_url": "https://storage.googleapis.com/bucket/test.mp3"
        },
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == 200
    assert "recording_id" in response.json()

def test_list_recordings(client, sample_token):
    response = client.get(
        "/api/recordings/list",
        headers={"Authorization": f"Bearer {sample_token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Quick Start Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with your credentials

# Database
alembic upgrade head

# Run locally
uvicorn app.main:app --reload

# Docker
docker-compose up

# Run tests
pytest

# Deploy
gcloud builds submit
gcloud run deploy api --image gcr.io/PROJECT_ID/api:latest
```

---

**Last Updated:** November 8, 2025
**FastAPI Version:** 0.104.1
**Python Version:** 3.10+
