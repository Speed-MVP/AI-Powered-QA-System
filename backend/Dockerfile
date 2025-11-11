FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Create startup script to handle migrations and server startup gracefully
RUN echo '#!/bin/sh\n\
set -e\n\
echo "=== Starting Application ==="\n\
echo "PORT: ${PORT:-8080}"\n\
echo "Checking environment variables..."\n\
[ -z "$DATABASE_URL" ] && echo "WARNING: DATABASE_URL not set"\n\
[ -z "$GCP_PROJECT_ID" ] && echo "WARNING: GCP_PROJECT_ID not set"\n\
[ -z "$JWT_SECRET" ] && echo "WARNING: JWT_SECRET not set"\n\
echo "Running database migrations..."\n\
if alembic upgrade head 2>&1; then\n\
  echo "Migrations completed successfully"\n\
else\n\
  echo "WARNING: Database migrations failed. Continuing anyway..."\n\
  echo "The application will start but database operations may fail."\n\
fi\n\
echo "Starting FastAPI server on port ${PORT:-8080}..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info --timeout-keep-alive 30\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]

