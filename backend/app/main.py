from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings
from app.database import init_db
from app.routes import (
    auth,
    recordings,
    evaluations,
    templates,
    health,
    fine_tuning,
    batch_processing,
    supervisor,
    teams,
    agents,
    imports,
)
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
# Parse CORS origins from environment variable (comma-separated)
cors_origins = [
    origin.strip() 
    for origin in settings.cors_origins.split(",") 
    if origin.strip()
]

logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Frontend URLs from environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Global exception handlers - CORS middleware will add headers automatically
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL configured: {'Yes' if settings.database_url != 'postgresql://placeholder:placeholder@localhost:5432/placeholder' else 'No (using placeholder)'}")
    logger.info(f"GCP Project ID configured: {'Yes' if settings.gcp_project_id != 'placeholder-project' else 'No (using placeholder)'}")
    logger.info(f"JWT Secret configured: {'Yes' if settings.jwt_secret != 'placeholder-jwt-secret-that-is-long-enough-for-validation-but-should-be-replaced' else 'No (using placeholder)'}")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Application will continue but database operations may fail")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI server...")

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(recordings.router, prefix="/api/recordings", tags=["recordings"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["evaluations"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(fine_tuning.router, prefix="/api", tags=["fine-tuning"])
app.include_router(batch_processing.router, prefix="/api/batch", tags=["batch-processing"])
app.include_router(supervisor.router, prefix="/api", tags=["supervisor"])
app.include_router(teams.router, prefix="/api", tags=["teams"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(imports.router, prefix="/api", tags=["bulk-import"])

@app.get("/")
async def root():
    return {"message": "AI QA Backend API - See /docs for Swagger UI"}

