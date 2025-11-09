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

In **Settings** → **Environment Variables**, add:

```
VITE_API_URL=https://your-backend-api-url.com
```

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
- Redeploy after adding/changing environment variables
- Variables are embedded at build time, not runtime

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
