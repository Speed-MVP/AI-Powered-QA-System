# Vercel Deployment Guide

This guide explains how to deploy the frontend to Vercel.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. The backend API deployed separately (e.g., on Railway, Render, or Google Cloud Run)
3. Environment variables configured

## Deployment Steps

### 1. Connect Your Repository to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your GitHub/GitLab/Bitbucket repository
4. Vercel will automatically detect the Vite project in the `web` directory

### 2. Configure Project Settings

In the Vercel project settings:
- **Root Directory:** Set to `web` (this tells Vercel to treat the `web` directory as the project root)
- **Framework Preset:** Vite (should be auto-detected)
- **Build Command:** `npm run build` (runs automatically in the `web` directory)
- **Output Directory:** `dist` (relative to `web` directory)
- **Install Command:** `npm install` (runs automatically in the `web` directory)

**Important:** After importing the repository, go to Settings → General → Root Directory and set it to `web`.

### 3. Set Environment Variables

In the Vercel project settings, add the following environment variables:

#### Required Environment Variables

```
VITE_API_URL=https://your-backend-api-url.com
```

#### Optional Environment Variables

If your frontend uses any other environment variables prefixed with `VITE_`, add them here.

**Note:** All frontend environment variables must be prefixed with `VITE_` to be accessible in the Vite build.

### 4. Deploy

1. Click "Deploy" in the Vercel dashboard
2. Vercel will build and deploy your application
3. You'll receive a deployment URL (e.g., `your-app.vercel.app`)

### 5. Update Backend CORS Settings

After deployment, update your backend API's CORS settings to allow your Vercel domain:

**For backend environment variables:**
```
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app
```

Or if using the backend config, add your Vercel URLs to the `cors_origins` environment variable (comma-separated).

### 6. Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Navigate to "Domains"
3. Add your custom domain
4. Update DNS records as instructed by Vercel
5. Update backend CORS to include your custom domain

## Environment Variables Reference

### Frontend (Vercel)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API URL | Yes |

### Backend (Separate Deployment)

| Variable | Description | Required |
|----------|-------------|----------|
| `CORS_ORIGINS` | Comma-separated list of allowed origins | Yes (for production) |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET` | JWT secret key | Yes |
| `GCP_PROJECT_ID` | Google Cloud Project ID | Yes |
| `GCP_BUCKET_NAME` | GCP Storage bucket name | Yes |
| `DEEPGRAM_API_KEY` | Deepgram API key | Yes |
| `GEMINI_API_KEY` | Gemini API key | Yes (if using Gemini) |
| And others as per backend requirements | | |

## Project Structure

```
.
├── web/                    # Frontend (deployed to Vercel)
│   ├── src/
│   ├── dist/              # Build output (generated)
│   ├── package.json
│   └── vite.config.ts
├── backend/               # Backend (deployed separately)
│   └── app/
├── vercel.json           # Vercel configuration
└── .vercelignore        # Files to ignore in Vercel deployment
```

## Build Process

1. Vercel runs `npm install` in the `web` directory
2. Vercel runs `npm run build` which:
   - Runs TypeScript compilation (`tsc`)
   - Builds the Vite application (`vite build`)
   - Outputs to `web/dist`
3. Vercel serves the `web/dist` directory

## Routing

The `vercel.json` configuration includes a rewrite rule that routes all requests to `index.html` to support client-side routing (React Router).

## Caching

Static assets (JS, CSS, images) are cached with a 1-year max-age for optimal performance.

## Troubleshooting

### Build Fails

1. Check build logs in Vercel dashboard
2. Ensure all dependencies are in `package.json`
3. Verify Node.js version is compatible (check `package.json` for `engines` field)

### Environment Variables Not Working

1. Ensure all frontend environment variables are prefixed with `VITE_`
2. Restart the deployment after adding environment variables
3. Verify variables are set in Vercel project settings (not in `vercel.json`)

### CORS Errors

1. Update backend `CORS_ORIGINS` to include your Vercel domain
2. Include both production and preview URLs:
   - `https://your-app.vercel.app`
   - `https://your-app-git-*.vercel.app` (for preview deployments)

### API Calls Failing

1. Verify `VITE_API_URL` is set correctly
2. Check that backend API is accessible from the internet
3. Verify backend CORS settings allow your Vercel domain

## Preview Deployments

Vercel automatically creates preview deployments for every pull request. These will have URLs like:
- `your-app-git-branch-name.vercel.app`

Make sure to update backend CORS to allow preview URLs if you want to test PRs against the production backend, or use a staging backend for preview deployments.

## Next Steps

1. Set up a production backend API (Railway, Render, or Google Cloud Run)
2. Configure environment variables in Vercel
3. Deploy and test
4. Set up a custom domain
5. Configure monitoring and error tracking (e.g., Sentry)

## Support

For issues or questions:
- Check Vercel documentation: https://vercel.com/docs
- Check build logs in Vercel dashboard
- Review environment variable configuration

