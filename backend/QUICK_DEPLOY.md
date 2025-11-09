# Quick Deploy Guide - Google Cloud Run

Simple 5-step deployment guide.

## Prerequisites Checklist

- [ ] Google Cloud account created
- [ ] Google Cloud SDK installed (`gcloud --version`)
- [ ] GCP project created
- [ ] Database (Neon/PostgreSQL) set up
- [ ] GCP Storage bucket created
- [ ] API keys ready (Deepgram, Gemini)

## Step 1: Setup Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Step 2: Create Storage Bucket and Service Account

```bash
# Create bucket
gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_BUCKET_NAME

# Grant Cloud Run service account access to Storage
# (This allows Cloud Run to use default credentials - no need for service account keys)
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.admin"
```

**Note**: If you use the default Cloud Run service account (recommended), you don't need to set `GCP_CLIENT_EMAIL` and `GCP_PRIVATE_KEY` in environment variables.

## Step 3: Configure Environment Variables

```bash
# Navigate to backend directory
cd backend

# Copy example file
cp .env.production.example .env.production

# Edit .env.production with your values
# Use your favorite editor: nano, vim, code, etc.
```

Fill in all the values in `.env.production`.

## Step 4: Deploy

### Option A: Using Web UI (No CLI Required) ⭐

See `DEPLOY_WITHOUT_CLI.md` for complete UI-based deployment guide.

**Quick steps:**
1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. Select **"Deploy one revision from a source repository"**
4. Connect your GitHub repository
5. Set Dockerfile location: `backend/Dockerfile`
6. Configure environment variables
7. Click **"Create"**

Cloud Run will automatically build and deploy!

### Option B: Using the deploy script (CLI)

```bash
# Make script executable
chmod +x deploy.sh

# Deploy
./deploy.sh
```

### Option B: Direct deployment (Simplest)

```bash
# Navigate to backend directory
cd backend

# Deploy directly (Cloud Build handles everything)
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
    --set-env-vars ENVIRONMENT="production" \
    --memory 2Gi \
    --cpu 2
```

**Note**: When using `--source .` from the `backend/` directory, Cloud Run automatically:
- Finds the Dockerfile in the current directory
- Sets the build context correctly
- Builds and deploys in one step

### Option C: Using Cloud Build UI

If you're using the Cloud Build UI:

1. **Branch**: `^main$` ✅ (correct)
2. **Build Type**: Dockerfile ✅
3. **Source location**: Change to `backend/Dockerfile` (not `/Dockerfile`)
4. **Working Directory**: Set to `backend/` if available in advanced settings

**Better option**: Use `cloudbuild.yaml`:
1. **Build Type**: Select "Cloud Build configuration file (yaml or json)"
2. **Location**: `backend/cloudbuild.yaml`

See `CLOUD_BUILD_SETUP.md` for detailed Cloud Build configuration.

## Step 5: Get Your API URL

After deployment, you'll see the service URL. Copy it:

```bash
# Get the URL
gcloud run services describe ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)'
```

Example: `https://ai-qa-backend-xxxxx-uc.a.run.app`

## Step 6: Update Frontend

1. Go to Vercel Dashboard
2. Settings → Environment Variables
3. Add: `VITE_API_URL=https://ai-qa-backend-xxxxx-uc.a.run.app`
4. Redeploy your frontend

## Step 7: Update Backend CORS

After deploying your frontend to Vercel:

```bash
# Update CORS with your Vercel domain
gcloud run services update ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --update-env-vars CORS_ORIGINS="https://your-app.vercel.app,http://localhost:5173"
```

## Troubleshooting

### Check Logs
```bash
gcloud run services logs read ai-qa-backend \
    --platform managed \
    --region us-central1 \
    --limit 50
```

### Test API
Visit: `https://your-api-url.run.app/docs`

### Common Issues

1. **Database connection fails**: Check DATABASE_URL and ensure database allows connections from Cloud Run
2. **Storage permission errors**: Ensure service account has Storage Admin role
3. **CORS errors**: Update CORS_ORIGINS with your frontend URL

## Next Steps

- Set up monitoring
- Configure custom domain (optional)
- Set up CI/CD for automatic deployments
- Enable Cloud CDN for better performance

## Need Help?

See `CLOUD_RUN_DEPLOYMENT.md` for detailed instructions.

