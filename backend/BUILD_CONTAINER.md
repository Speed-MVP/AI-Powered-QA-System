# How to Build Container Image for Cloud Run

This guide explains different ways to build your container image for Google Cloud Run.

## Method 1: Automatic Build & Deploy (Easiest - Recommended)

Cloud Run can build your container automatically from source code:

```bash
# Navigate to backend directory
cd backend

# Deploy directly - Cloud Run builds and deploys automatically
gcloud run deploy ai-qa-backend \
    --source . \
    --platform managed \
    --region asia-southeast1 \
    --allow-unauthenticated
```

**What this does:**
- Automatically builds your Docker image using the Dockerfile
- Pushes the image to Container Registry
- Deploys to Cloud Run
- No manual build step needed!

## Method 2: Build with Cloud Build (Manual)

Build the image first, then deploy:

```bash
# Navigate to backend directory
cd backend

# Build the image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-qa-backend

# Deploy the built image
gcloud run deploy ai-qa-backend \
    --image gcr.io/YOUR_PROJECT_ID/ai-qa-backend \
    --platform managed \
    --region asia-southeast1 \
    --allow-unauthenticated
```

**Replace `YOUR_PROJECT_ID`** with your actual GCP project ID.

## Method 3: Build Locally with Docker

Build the image on your local machine:

```bash
# Navigate to backend directory
cd backend

# Build the image
docker build -t ai-qa-backend .

# Tag for Google Container Registry
docker tag ai-qa-backend gcr.io/YOUR_PROJECT_ID/ai-qa-backend

# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/ai-qa-backend
```

Then in Cloud Run UI, use: `gcr.io/YOUR_PROJECT_ID/ai-qa-backend`

## Method 4: Using Cloud Build Configuration File

Use the `cloudbuild.yaml` file for more control:

```bash
# From project root
gcloud builds submit --config=backend/cloudbuild.yaml
```

This builds, tags, and optionally deploys automatically.

## For Your Current Situation (Cloud Run UI)

Since you're in the Cloud Run UI:

### Option A: Use Automatic Build (Recommended)

1. **Don't use the UI** - Use command line instead:
   ```bash
   cd backend
   gcloud run deploy ai-qa-backend --source . --region asia-southeast1
   ```

2. This automatically:
   - Builds the container from your Dockerfile
   - Pushes to Container Registry
   - Deploys to Cloud Run
   - Returns the service URL

### Option B: Build First, Then Use UI

1. **Build the image:**
   ```bash
   cd backend
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-qa-backend
   ```

2. **In Cloud Run UI:**
   - Container image URL: `gcr.io/YOUR_PROJECT_ID/ai-qa-backend`
   - Click "Select" and choose the image
   - Configure other settings
   - Click "Deploy"

## Getting Your Project ID

Find your project ID:

```bash
gcloud config get-value project
```

Or check in the Google Cloud Console (top right shows project name).

## Setting Environment Variables

After building, set environment variables in Cloud Run:

### Via Command Line:
```bash
gcloud run services update ai-qa-backend \
    --region asia-southeast1 \
    --update-env-vars DATABASE_URL="your-db-url" \
    --update-env-vars GCP_PROJECT_ID="your-project-id" \
    --update-env-vars GCP_BUCKET_NAME="your-bucket-name" \
    --update-env-vars JWT_SECRET="your-jwt-secret" \
    --update-env-vars DEEPGRAM_API_KEY="your-key" \
    --update-env-vars GEMINI_API_KEY="your-key" \
    --update-env-vars CORS_ORIGINS="http://localhost:5173"
```

### Via UI:
1. In Cloud Run service page
2. Click "Edit & Deploy New Revision"
3. Go to "Variables & Secrets" tab
4. Add environment variables
5. Click "Deploy"

## Quick Start (Recommended)

The easiest way for your first deployment:

```bash
# 1. Navigate to backend
cd backend

# 2. Deploy (builds automatically)
gcloud run deploy ai-qa-backend \
    --source . \
    --platform managed \
    --region asia-southeast1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL="your-db-url" \
    --set-env-vars GCP_PROJECT_ID="your-project-id" \
    --set-env-vars GCP_BUCKET_NAME="your-bucket-name" \
    --set-env-vars JWT_SECRET="your-jwt-secret" \
    --set-env-vars DEEPGRAM_API_KEY="your-key" \
    --set-env-vars GEMINI_API_KEY="your-key" \
    --set-env-vars CORS_ORIGINS="http://localhost:5173" \
    --memory 2Gi \
    --cpu 2

# 3. Get the service URL
gcloud run services describe ai-qa-backend \
    --region asia-southeast1 \
    --format 'value(status.url)'
```

## Troubleshooting

### "Permission denied" errors
```bash
# Ensure you're authenticated
gcloud auth login

# Set the correct project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### "Dockerfile not found"
- Make sure you're in the `backend/` directory
- Or use `--source backend` from project root

### Build takes too long
- First build is slower (downloading base image)
- Subsequent builds are faster (layers are cached)

## Next Steps

After building and deploying:
1. Get your service URL
2. Update Vercel with `VITE_API_URL`
3. Test the API at `https://your-service.run.app/docs`
4. Update CORS settings with your Vercel domain

## Additional Resources

- See `QUICK_DEPLOY.md` for complete deployment guide
- See `CLOUD_BUILD_SETUP.md` for Cloud Build triggers
- See `deploy.sh` for automated deployment script

