# Google Cloud Run Deployment Guide

Simple guide to deploy the FastAPI backend to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account** - Sign up at https://cloud.google.com
2. **Google Cloud SDK (gcloud)** - Install from https://cloud.google.com/sdk/docs/install
3. **Docker** - For local testing (optional)
4. **GCP Project** - Create a project in Google Cloud Console

## Step 1: Install Google Cloud SDK

```bash
# Download and install gcloud CLI
# Follow instructions at: https://cloud.google.com/sdk/docs/install

# Verify installation
gcloud --version

# Login to Google Cloud
gcloud auth login

# Set your project (replace PROJECT_ID with your actual project ID)
gcloud config set project PROJECT_ID
```

## Step 2: Enable Required APIs

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com
```

## Step 3: Set Up GCP Services

### 3.1 Create GCP Storage Bucket

```bash
# Create a bucket for audio files
gsutil mb -p PROJECT_ID -l us-central1 gs://BUCKET_NAME

# Make bucket private (recommended)
gsutil iam ch allUsers:objectViewer gs://BUCKET_NAME
```

### 3.2 Set Up Service Account

```bash
# Create service account
gcloud iam service-accounts create ai-qa-backend \
    --display-name="AI QA Backend Service Account"

# Grant Storage Admin role
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:ai-qa-backend@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=ai-qa-backend@PROJECT_ID.iam.gserviceaccount.com
```

## Step 4: Prepare Environment Variables

Create a file with all environment variables needed for Cloud Run:

```bash
# Set these variables (replace with your actual values)
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
export GCP_PROJECT_ID="your-project-id"
export GCP_BUCKET_NAME="your-bucket-name"
export GCP_CLIENT_EMAIL="ai-qa-backend@PROJECT_ID.iam.gserviceaccount.com"
export GCP_PRIVATE_KEY="$(cat key.json | jq -r '.private_key')"
export JWT_SECRET="your-super-secret-jwt-key-min-32-chars"
export DEEPGRAM_API_KEY="your-deepgram-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM="your-email@gmail.com"
export CORS_ORIGINS="https://your-frontend.vercel.app,http://localhost:5173"
export ENVIRONMENT="production"
export LOG_LEVEL="INFO"
```

## Step 5: Build and Deploy

### Option A: Deploy from Source (Recommended)

```bash
# Navigate to backend directory
cd backend

# Deploy to Cloud Run (this builds and deploys in one step)
gcloud run deploy ai-qa-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL="$DATABASE_URL" \
    --set-env-vars GCP_PROJECT_ID="$GCP_PROJECT_ID" \
    --set-env-vars GCP_BUCKET_NAME="$GCP_BUCKET_NAME" \
    --set-env-vars GCP_CLIENT_EMAIL="$GCP_CLIENT_EMAIL" \
    --set-env-vars GCP_PRIVATE_KEY="$GCP_PRIVATE_KEY" \
    --set-env-vars JWT_SECRET="$JWT_SECRET" \
    --set-env-vars DEEPGRAM_API_KEY="$DEEPGRAM_API_KEY" \
    --set-env-vars GEMINI_API_KEY="$GEMINI_API_KEY" \
    --set-env-vars SMTP_HOST="$SMTP_HOST" \
    --set-env-vars SMTP_PORT="$SMTP_PORT" \
    --set-env-vars SMTP_USER="$SMTP_USER" \
    --set-env-vars SMTP_PASSWORD="$SMTP_PASSWORD" \
    --set-env-vars SMTP_FROM="$SMTP_FROM" \
    --set-env-vars CORS_ORIGINS="$CORS_ORIGINS" \
    --set-env-vars ENVIRONMENT="$ENVIRONMENT" \
    --set-env-vars LOG_LEVEL="$LOG_LEVEL" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10
```

### Option B: Build Docker Image First

```bash
# Build the image
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-qa-backend

# Deploy the image
gcloud run deploy ai-qa-backend \
    --image gcr.io/PROJECT_ID/ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL="$DATABASE_URL" \
    # ... (same env vars as above)
```

## Step 6: Get Your API URL

After deployment, Cloud Run will provide you with a URL:

```bash
# Get the service URL
gcloud run services describe ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)'
```

Example output: `https://ai-qa-backend-xxxxx-uc.a.run.app`

## Step 7: Update Frontend

Update your Vercel environment variable:

```
VITE_API_URL=https://ai-qa-backend-xxxxx-uc.a.run.app
```

## Step 8: Run Database Migrations

Migrations run automatically on startup (see Dockerfile), but you can also run them manually:

```bash
# Connect to the Cloud Run service
gcloud run services update ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --update-env-vars RUN_MIGRATIONS=true
```

## Troubleshooting

### Check Logs

```bash
# View logs
gcloud run services logs read ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --limit 50
```

### Update Environment Variables

```bash
# Update a single variable
gcloud run services update ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --update-env-vars CORS_ORIGINS="https://new-frontend.vercel.app"
```

### Redeploy After Code Changes

```bash
# Simply redeploy (Cloud Build will rebuild the image)
gcloud run deploy ai-qa-backend \
    --source . \
    --platform managed \
    --region us-central1
```

## Cost Optimization

- **Memory**: Start with 512Mi, increase if needed
- **CPU**: Start with 1 CPU, increase for faster processing
- **Max Instances**: Set based on expected traffic
- **Min Instances**: Set to 0 to scale to zero when not in use (saves costs)

## Security Notes

1. **Never commit secrets** to the repository
2. **Use Secret Manager** for sensitive data (recommended for production)
3. **Set up IAM roles** properly
4. **Enable Cloud Armor** for DDoS protection (optional)
5. **Use VPC** for private database connections (optional)

## Next Steps

1. Set up monitoring with Cloud Monitoring
2. Configure alerts for errors
3. Set up CI/CD with Cloud Build
4. Enable Cloud CDN for better performance
5. Set up custom domain (optional)

## Quick Deploy Script

Create a `deploy.sh` file:

```bash
#!/bin/bash

# Load environment variables
source .env.production

# Deploy to Cloud Run
gcloud run deploy ai-qa-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL="$DATABASE_URL" \
    --set-env-vars GCP_PROJECT_ID="$GCP_PROJECT_ID" \
    --set-env-vars GCP_BUCKET_NAME="$GCP_BUCKET_NAME" \
    --set-env-vars JWT_SECRET="$JWT_SECRET" \
    --set-env-vars DEEPGRAM_API_KEY="$DEEPGRAM_API_KEY" \
    --set-env-vars GEMINI_API_KEY="$GEMINI_API_KEY" \
    --set-env-vars CORS_ORIGINS="$CORS_ORIGINS" \
    --memory 2Gi \
    --cpu 2

echo "Deployment complete! URL:"
gcloud run services describe ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)'
```

Make it executable and run:
```bash
chmod +x deploy.sh
./deploy.sh
```

