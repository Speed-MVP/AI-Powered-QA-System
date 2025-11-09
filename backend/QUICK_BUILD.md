# Quick Guide: Build Container Image for Cloud Run

## Easiest Method: Automatic Build & Deploy

**From the `backend/` directory:**

```bash
cd backend
gcloud run deploy ai-qa-backend --source . --region asia-southeast1
```

This automatically:
1. ✅ Builds your container from Dockerfile
2. ✅ Pushes to Container Registry  
3. ✅ Deploys to Cloud Run
4. ✅ Returns the service URL

**No manual build step needed!**

## Alternative: Build First, Then Deploy via UI

If you want to build the image first and then use the Cloud Run UI:

### Step 1: Build the Image

```bash
cd backend

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-qa-backend
```

**Get your project ID:**
```bash
gcloud config get-value project
```

### Step 2: Use in Cloud Run UI

1. In Cloud Run UI, click "Select" next to Container image URL
2. Enter: `gcr.io/YOUR_PROJECT_ID/ai-qa-backend`
3. Configure other settings (memory, CPU, environment variables)
4. Click "Deploy"

## Complete Deployment with Environment Variables

```bash
cd backend

gcloud run deploy ai-qa-backend \
    --source . \
    --platform managed \
    --region asia-southeast1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL="your-database-url" \
    --set-env-vars GCP_PROJECT_ID="your-project-id" \
    --set-env-vars GCP_BUCKET_NAME="your-bucket-name" \
    --set-env-vars JWT_SECRET="your-jwt-secret" \
    --set-env-vars DEEPGRAM_API_KEY="your-deepgram-key" \
    --set-env-vars GEMINI_API_KEY="your-gemini-key" \
    --set-env-vars CORS_ORIGINS="http://localhost:5173" \
    --memory 2Gi \
    --cpu 2
```

## What Happens During Build

1. **Cloud Build** reads your `Dockerfile`
2. **Builds** the container image layer by layer
3. **Installs** Python dependencies from `requirements.txt`
4. **Copies** your application code
5. **Pushes** the image to `gcr.io/YOUR_PROJECT_ID/ai-qa-backend`
6. **Deploys** to Cloud Run

## After Deployment

1. **Get your service URL:**
   ```bash
   gcloud run services describe ai-qa-backend \
       --region asia-southeast1 \
       --format 'value(status.url)'
   ```

2. **Test the API:**
   Visit: `https://your-service-url.run.app/docs`

3. **Update Vercel:**
   Set `VITE_API_URL` to your Cloud Run URL

## Troubleshooting

### "Permission denied"
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### "API not enabled"
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### "Dockerfile not found"
- Make sure you're in the `backend/` directory
- Or the Dockerfile exists at `backend/Dockerfile`

## Need More Details?

See `BUILD_CONTAINER.md` for all build methods.

