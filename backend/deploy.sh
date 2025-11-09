#!/bin/bash

# Google Cloud Run Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Deploying to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project set. Please run: gcloud config set project PROJECT_ID"
    exit 1
fi

echo "📍 Project ID: $PROJECT_ID"

# Service name
SERVICE_NAME="ai-qa-backend"
REGION="us-central1"

# Check if .env file exists
if [ ! -f ".env.production" ]; then
    echo "⚠️  Warning: .env.production not found"
    echo "📝 Please create .env.production with all required environment variables"
    echo "   See CLOUD_RUN_DEPLOYMENT.md for details"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Load environment variables if file exists
if [ -f ".env.production" ]; then
    set -a
    source .env.production
    set +a
fi

# Required environment variables
REQUIRED_VARS=(
    "DATABASE_URL"
    "GCP_PROJECT_ID"
    "GCP_BUCKET_NAME"
    "JWT_SECRET"
    "DEEPGRAM_API_KEY"
)

# Check for required variables
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo "📝 Please set these in .env.production or as environment variables"
    exit 1
fi

# Set default CORS if not set
if [ -z "$CORS_ORIGINS" ]; then
    CORS_ORIGINS="http://localhost:5173"
    echo "⚠️  CORS_ORIGINS not set, using default: $CORS_ORIGINS"
fi

# Build and deploy
echo "🔨 Building and deploying..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL="$DATABASE_URL" \
    --set-env-vars GCP_PROJECT_ID="$GCP_PROJECT_ID" \
    --set-env-vars GCP_BUCKET_NAME="$GCP_BUCKET_NAME" \
    --set-env-vars JWT_SECRET="$JWT_SECRET" \
    --set-env-vars DEEPGRAM_API_KEY="$DEEPGRAM_API_KEY" \
    --set-env-vars CORS_ORIGINS="$CORS_ORIGINS" \
    ${GCP_CLIENT_EMAIL:+--set-env-vars GCP_CLIENT_EMAIL="$GCP_CLIENT_EMAIL"} \
    ${GCP_PRIVATE_KEY:+--set-env-vars GCP_PRIVATE_KEY="$GCP_PRIVATE_KEY"} \
    ${GEMINI_API_KEY:+--set-env-vars GEMINI_API_KEY="$GEMINI_API_KEY"} \
    ${CLAUDE_API_KEY:+--set-env-vars CLAUDE_API_KEY="$CLAUDE_API_KEY"} \
    ${SMTP_HOST:+--set-env-vars SMTP_HOST="$SMTP_HOST"} \
    ${SMTP_PORT:+--set-env-vars SMTP_PORT="$SMTP_PORT"} \
    ${SMTP_USER:+--set-env-vars SMTP_USER="$SMTP_USER"} \
    ${SMTP_PASSWORD:+--set-env-vars SMTP_PASSWORD="$SMTP_PASSWORD"} \
    ${SMTP_FROM:+--set-env-vars SMTP_FROM="$SMTP_FROM"} \
    --set-env-vars ENVIRONMENT="production" \
    --set-env-vars LOG_LEVEL="${LOG_LEVEL:-INFO}" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo "   1. Update Vercel environment variable: VITE_API_URL=$SERVICE_URL"
echo "   2. Update backend CORS_ORIGINS with your Vercel domain"
echo "   3. Test the API: $SERVICE_URL/docs"

