FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Simple startup command with increased request body size limit (500MB)
# --limit-max-requests: max concurrent requests
# Note: Request body size limit is controlled by uvicorn's default (1MB) but we handle it in middleware
# For Cloud Run, we rely on the middleware to handle large uploads via streaming
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --limit-max-requests 1000"]
