# Dockerfile Explanation

This document explains the optimized Dockerfile for Cloud Run deployment.

## Key Optimizations

### 1. Layer Caching
- Requirements are copied and installed before application code
- Changes to code don't require reinstalling dependencies
- Faster rebuilds during development

### 2. Python Environment Variables
```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```
- `PYTHONUNBUFFERED=1`: Ensures Python output is sent directly to stdout/stderr
- `PYTHONDONTWRITEBYTECODE=1`: Prevents creation of .pyc files
- `PIP_NO_CACHE_DIR=1`: Reduces image size by not caching pip packages
- `PIP_DISABLE_PIP_VERSION_CHECK=1`: Speeds up pip operations

### 3. System Dependencies
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
```
- `--no-install-recommends`: Installs only essential packages
- `libpq-dev`: Required for psycopg2 (PostgreSQL driver)
- Cleanup removes apt cache to reduce image size

### 4. Port Configuration
```dockerfile
ENV PORT=8080
EXPOSE 8080
```
- Cloud Run sets PORT dynamically, but we provide a default
- Application reads `${PORT:-8080}` for flexibility

### 5. Startup Command
```dockerfile
CMD sh -c "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
```
- Runs database migrations on startup
- Uses `exec` to replace shell process with uvicorn (better signal handling)
- Listens on all interfaces (0.0.0.0) for Cloud Run
- Single worker (Cloud Run scales by instances)

## Build the Image

### Local Build (for testing)
```bash
cd backend
docker build -t ai-qa-backend .
docker run -p 8080:8080 ai-qa-backend
```

### Build for Cloud Run
```bash
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-qa-backend
```

### Automatic Build & Deploy
```bash
cd backend
gcloud run deploy ai-qa-backend --source .
```

## Image Size Optimization

The current Dockerfile creates an optimized image by:
- Using Python slim base image
- Removing apt cache after installation
- Not caching pip packages
- Installing only necessary system dependencies

## Security Considerations

- Uses official Python base image
- Minimal system dependencies
- No root user operations (Cloud Run handles security)
- Environment variables for sensitive data (not in image)

## Cloud Run Specific Features

1. **Health Checks**: Cloud Run automatically checks `/health` endpoint
2. **Scaling**: Cloud Run scales instances (not workers within instance)
3. **Port Binding**: Application listens on PORT environment variable
4. **Graceful Shutdown**: Uvicorn handles SIGTERM signals properly

## Troubleshooting

### Build fails
- Check Dockerfile syntax
- Verify all files exist (requirements.txt, etc.)
- Check Docker daemon is running

### Container won't start
- Check logs: `gcloud run services logs read ai-qa-backend`
- Verify PORT environment variable
- Check database connectivity

### Migrations fail
- Verify DATABASE_URL is set correctly
- Check database permissions
- Ensure database is accessible from Cloud Run

## Further Optimization (Optional)

### Multi-stage Build
For even smaller images, you could use multi-stage builds:
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

However, for Cloud Run, the current single-stage build is sufficient and simpler.

