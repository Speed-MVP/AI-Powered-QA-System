# Deploy to Cloud Run Without CLI (Using Web UI)

You can build and deploy your container image entirely through the Google Cloud Console web interface - no CLI needed!

## Method 1: Cloud Build + Cloud Run UI (Recommended)

### Step 1: Push Your Code to GitHub

1. Make sure your code is pushed to GitHub/GitLab/Bitbucket
2. Your repository should have the `backend/` directory with:
   - `Dockerfile`
   - `requirements.txt`
   - All application code

### Step 2: Set Up Cloud Build (One-Time Setup)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **Cloud Build** → **Triggers**
3. Click **"Create Trigger"**
4. Configure:
   - **Name**: `build-backend`
   - **Event**: Push to a branch
   - **Branch**: `^main$`
   - **Source**: Connect your repository (GitHub/GitLab/Bitbucket)
   - **Configuration**: **Cloud Build configuration file (yaml or json)**
   - **Location**: `backend/cloudbuild.yaml`
5. Click **"Create"**

### Step 3: Deploy via Cloud Run UI

1. Go to [Cloud Run](https://console.cloud.google.com/run)
2. Click **"Create Service"** or **"Deploy"**
3. Configure the service:
   - **Service name**: `ai-qa-backend`
   - **Region**: `asia-southeast1` (or your preferred region)
   - **Deploy one revision from an existing container image**
   - **Container image URL**: Select the image built by Cloud Build
     - It will be: `gcr.io/YOUR_PROJECT_ID/ai-qa-backend:latest`
   - Click **"Select"** and choose the image
4. Click **"Next"** or **"Container"** tab
5. Set **Container port**: `8080`
6. Click **"Variables & Secrets"** tab
7. Add environment variables:
   - `DATABASE_URL` = your database URL
   - `GCP_PROJECT_ID` = your project ID
   - `GCP_BUCKET_NAME` = your bucket name
   - `JWT_SECRET` = your JWT secret
   - `DEEPGRAM_API_KEY` = your Deepgram key
   - `GEMINI_API_KEY` = your Gemini key
   - `CORS_ORIGINS` = `http://localhost:5173`
   - `ENVIRONMENT` = `production`
   - `LOG_LEVEL` = `INFO`
8. Click **"Networking"** tab:
   - **Allow unauthenticated invocations**: ✅ Checked
9. Click **"Resources"** or expand "Container" settings:
   - **Memory**: `2 GiB`
   - **CPU**: `2`
   - **Timeout**: `300 seconds`
10. Click **"Create"** or **"Deploy"**

That's it! Your service will be deployed.

## Method 2: Build in Cloud Build UI, Then Deploy

### Step 1: Build Container Image in Cloud Build UI

1. Go to [Cloud Build](https://console.cloud.google.com/cloud-build)
2. Click **"Create Build"** or **"Run"**
3. Select your source:
   - **Source**: GitHub/GitLab repository
   - **Branch**: `main`
4. Configure build:
   - **Build configuration**: **Cloud Build configuration file (yaml or json)**
   - **Cloud Build configuration file location**: `backend/cloudbuild.yaml`
   - OR use **Dockerfile**:
     - **Dockerfile location**: `backend/Dockerfile`
     - **Docker context**: `backend/`
5. Click **"Run"** or **"Start build"**
6. Wait for build to complete (5-10 minutes for first build)

### Step 2: Deploy to Cloud Run

1. Go to [Cloud Run](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. Select **"Deploy one revision from an existing container image"**
4. Container image URL: 
   - Click **"Select"**
   - Choose: `gcr.io/YOUR_PROJECT_ID/ai-qa-backend:latest`
5. Configure service (same as Method 1, steps 4-10)

## Method 3: Use Cloud Run's Built-in Build

Cloud Run can build directly from source code in the UI:

### Step 1: Deploy from Source

1. Go to [Cloud Run](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. Select **"Deploy one revision from a source repository"**
4. Connect your repository (GitHub/GitLab/Bitbucket)
5. Configure:
   - **Source repository**: Your repo
   - **Branch**: `main`
   - **Build type**: **Dockerfile**
   - **Dockerfile location**: `backend/Dockerfile`
   - **Docker context**: `backend/`
6. Click **"Next"**
7. Configure service settings (port, environment variables, etc.)
8. Click **"Create"**

Cloud Run will:
- Build the container automatically
- Push to Container Registry
- Deploy the service

## Setting Environment Variables in UI

1. In Cloud Run service page
2. Click **"Edit & Deploy New Revision"**
3. Go to **"Variables & Secrets"** tab
4. Click **"Add Variable"** for each:
   - `DATABASE_URL`
   - `GCP_PROJECT_ID`
   - `GCP_BUCKET_NAME`
   - `JWT_SECRET`
   - `DEEPGRAM_API_KEY`
   - `GEMINI_API_KEY`
   - `CORS_ORIGINS`
   - `ENVIRONMENT` = `production`
   - `LOG_LEVEL` = `INFO`
5. Click **"Deploy"**

## Getting Your Service URL

After deployment:

1. Go to [Cloud Run Services](https://console.cloud.google.com/run)
2. Click on your service: `ai-qa-backend`
3. The **URL** is displayed at the top
4. Copy this URL
5. Use it in Vercel as `VITE_API_URL`

## Updating Your Service (Redeploy)

### Option 1: Rebuild via Cloud Build Trigger

1. Push changes to GitHub
2. Cloud Build trigger automatically builds new image
3. Go to Cloud Run → Your service
4. Click **"Edit & Deploy New Revision"**
5. Select the new image
6. Click **"Deploy"**

### Option 2: Rebuild in Cloud Build UI

1. Go to Cloud Build
2. Click **"Create Build"**
3. Run the build again
4. Go to Cloud Run and deploy the new image

### Option 3: Deploy from Source Again

1. Go to Cloud Run → Your service
2. Click **"Edit & Deploy New Revision"**
3. Change source to your repository
4. Cloud Run rebuilds automatically
5. Click **"Deploy"**

## Viewing Logs

1. Go to Cloud Run → Your service
2. Click **"Logs"** tab
3. View real-time logs
4. Filter by severity, time, etc.

## Monitoring

1. Go to Cloud Run → Your service
2. Click **"Metrics"** tab
3. View:
   - Request count
   - Latency
   - Error rate
   - Instance count

## Troubleshooting

### Build Fails

1. Check Cloud Build logs
2. Verify Dockerfile exists at `backend/Dockerfile`
3. Check that all files are in the repository

### Service Won't Start

1. Check Cloud Run logs
2. Verify environment variables are set
3. Check database connectivity
4. Verify PORT is set to 8080

### Can't Find Container Image

1. Go to Container Registry
2. Check if image exists: `gcr.io/YOUR_PROJECT_ID/ai-qa-backend`
3. Make sure Cloud Build completed successfully

## Quick Checklist

- [ ] Code pushed to GitHub
- [ ] Cloud Build trigger created (optional)
- [ ] Container image built
- [ ] Cloud Run service created
- [ ] Environment variables set
- [ ] Service deployed
- [ ] Service URL copied
- [ ] Vercel updated with API URL
- [ ] CORS updated with Vercel domain

## No CLI Required!

All of this can be done through the Google Cloud Console web interface. You only need:
- Google Cloud account
- Web browser
- Your code in a Git repository

That's it! No command line needed.

