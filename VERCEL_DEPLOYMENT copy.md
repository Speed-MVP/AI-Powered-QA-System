# Vercel Deployment Guide

This guide explains how to deploy the frontend to Vercel.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. The backend API deployed separately (e.g., on Railway, Render, or Google Cloud Run)
3. Environment variables configured

## Quick Setup

### 1. Connect Repository to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your GitHub/GitLab/Bitbucket repository

### 2. Configure Project Settings

**IMPORTANT:** In Vercel project settings:

1. Go to **Settings** → **General**
2. Set **Root Directory** to `web`
3. **Framework Preset** should auto-detect as "Vite"
4. **Build Command:** `npm run build` (auto-detected)
5. **Output Directory:** `dist` (auto-detected)
6. **Install Command:** `npm install` (auto-detected)

Vercel will automatically detect the Vite project and configure build settings.

### 3. Set Environment Variables

**CRITICAL:** You must set `VITE_API_URL` in Vercel for production to work!

1. Go to **Settings** → **Environment Variables**
2. Click **Add New**
3. Add the following:

**Key:** `VITE_API_URL`  
**Value:** Your deployed backend URL (e.g., `https://your-service-123456.a.run.app` for Cloud Run)

**Important:**
- ⚠️ **If you don't set this, the app will try to use `http://localhost:8000` which won't work in production!**
- The URL should be your deployed backend (Cloud Run, Railway, Render, etc.)
- Do NOT include a port number unless your backend uses a non-standard port
- Must start with `https://` for production
- After adding, you MUST redeploy for the change to take effect (Vite embeds env vars at build time)

### 4. Deploy

Click **Deploy**. Vercel will:
- Install dependencies
- Build the project
- Deploy to a production URL

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL (e.g., `https://your-api.railway.app`) |

**Note:** All frontend environment variables must be prefixed with `VITE_` to be accessible in the build.

## Backend CORS Configuration

After deployment, update your backend's `CORS_ORIGINS` environment variable:

```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
```

## Troubleshooting

### Build Fails

- Check that **Root Directory** is set to `web` in Vercel settings
- Verify `package.json` exists in the `web` directory
- Check build logs for specific errors

### Environment Variables Not Working

- Ensure variables are prefixed with `VITE_`
- **You MUST redeploy after adding/changing environment variables** (they're embedded at build time, not runtime)
- Check that `VITE_API_URL` is set correctly in Vercel dashboard
- Verify the backend URL is accessible (try opening it in a browser)
- Check browser console for API errors - if you see requests to `localhost:8000`, the env var wasn't set

### API Calls Going to localhost:8000

If your deployed app is trying to call `http://localhost:8000`:
1. **VITE_API_URL is not set in Vercel** - Go to Settings → Environment Variables and add it
2. **You didn't redeploy after adding the env var** - Trigger a new deployment
3. **Check the deployment logs** - Look for the build to confirm the env var was available during build

### Routing Issues

The `vercel.json` file handles client-side routing by redirecting all routes to `index.html`. This is already configured.

## Project Structure

```
.
├── web/                 # Frontend (Vercel deploys this)
│   ├── src/
│   ├── dist/           # Build output (generated)
│   ├── package.json
│   ├── vite.config.ts
│   └── vercel.json     # SPA routing config
└── backend/            # Backend (deployed separately)
```

## Next Steps

1. Deploy backend API separately
2. Set `VITE_API_URL` in Vercel
3. Update backend CORS settings
4. Test the deployed application
