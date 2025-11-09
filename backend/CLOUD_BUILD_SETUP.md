# Google Cloud Build Setup Guide

This guide helps you set up Cloud Build for automatic deployments to Cloud Run.

## Option 1: Using Cloud Build UI (What you're seeing)

### Configuration in the UI:

1. **Branch**: `^main$` ✅ (correct - matches main branch)

2. **Build Type**: Dockerfile ✅ (correct)

3. **Source location**: Change from `/Dockerfile` to:
   ```
   backend/Dockerfile
   ```
   **Important**: Since your Dockerfile is in the `backend/` directory, you need to specify the path relative to the repository root.

4. **Docker build context**: The build context should be the `backend/` directory. You may need to configure this separately or use a `cloudbuild.yaml` file.

### Recommended: Use cloudbuild.yaml

Instead of configuring in the UI, use the `cloudbuild.yaml` file for more control:

1. In Cloud Build UI, change **Build Type** to "Cloud Build configuration file (yaml or json)"
2. Set **Location** to: `backend/cloudbuild.yaml`

This gives you better control over the build process.

## Option 2: Using gcloud CLI (Recommended for automation)

### Create a Cloud Build Trigger

```bash
# Create a trigger that builds on push to main branch
gcloud builds triggers create github \
    --name="deploy-backend" \
    --repo-name="YOUR_REPO_NAME" \
    --repo-owner="YOUR_GITHUB_USERNAME" \
    --branch-pattern="^main$" \
    --build-config="backend/cloudbuild.yaml" \
    --region="us-central1"
```

### Manual Build

```bash
# Build and deploy manually
gcloud builds submit --config=backend/cloudbuild.yaml
```

## Option 3: Direct Deployment (Simplest)

For quick deployments, use the `deploy.sh` script or direct gcloud commands:

```bash
cd backend
gcloud run deploy ai-qa-backend --source .
```

This automatically:
- Builds the Docker image
- Pushes to Container Registry
- Deploys to Cloud Run

## Configuration Details

### If using UI with Dockerfile:

**Source location**: `backend/Dockerfile`

**Build context**: You may need to specify this in advanced settings or use a `cloudbuild.yaml` file.

### Environment Variables

Set these in Cloud Run (not in Cloud Build):

```bash
gcloud run services update ai-qa-backend \
    --update-env-vars DATABASE_URL="..." \
    --update-env-vars GCP_PROJECT_ID="..." \
    # ... other vars
```

Or set them during initial deployment:

```bash
gcloud run deploy ai-qa-backend \
    --source backend \
    --set-env-vars DATABASE_URL="..." \
    # ... other vars
```

## Troubleshooting

### Build fails with "Dockerfile not found"

- Make sure **Source location** is `backend/Dockerfile` (not `/Dockerfile`)
- Or use the `cloudbuild.yaml` file which specifies the correct path

### Build context issues

- The Dockerfile expects files relative to the `backend/` directory
- Use `cloudbuild.yaml` to set the correct build context: `backend`

### Recommended Setup

1. **Use `cloudbuild.yaml`** for Cloud Build triggers
2. **Use `deploy.sh`** for manual deployments
3. **Set environment variables** in Cloud Run (not in build config)

## Quick Start

1. **For UI setup**: Change source location to `backend/Dockerfile`
2. **For automation**: Use `backend/cloudbuild.yaml`
3. **For manual deploy**: Use `./deploy.sh` in the backend directory

## Next Steps

After the build succeeds:
1. Get your service URL
2. Update Vercel with the API URL
3. Update CORS settings in Cloud Run

See `QUICK_DEPLOY.md` for complete deployment instructions.

