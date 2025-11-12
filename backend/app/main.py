from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
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

# Add common variations of the origin (with and without www)
# This helps catch cases where the origin might be slightly different
enhanced_origins = set(cors_origins)
for origin in cors_origins:
    if origin.startswith("https://"):
        # Add www version if not present
        if "www." not in origin:
            enhanced_origins.add(origin.replace("https://", "https://www."))
        # Add non-www version if www is present
        elif origin.startswith("https://www."):
            enhanced_origins.add(origin.replace("https://www.", "https://"))

cors_origins = list(enhanced_origins)

logger.info(f"CORS origins configured: {cors_origins}")

# Add CORS logging middleware to help debug CORS issues
class CORSLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        origin = request.headers.get("origin")
        if origin:
            logger.debug(f"Incoming request from origin: {origin}, path: {request.url.path}, method: {request.method}")
            if origin not in cors_origins:
                logger.warning(f"Request from origin '{origin}' not in allowed CORS origins: {cors_origins}")
        response = await call_next(request)
        return response

app.add_middleware(CORSLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Frontend URLs from environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
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
    logger.info("Database URL configured: Yes")
    logger.info("GCP Project ID configured: Yes")
    logger.info("JWT Secret configured: Yes")
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

