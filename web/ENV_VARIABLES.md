# Environment Variables for Vercel Deployment

## Required Environment Variables

Set these in your Vercel project settings (Settings → Environment Variables):

### Backend API
```
VITE_API_URL=https://your-backend-api-url.com
```
The URL of your deployed FastAPI backend (e.g., Railway, Render, or Google Cloud Run).

## Important Notes

1. **All frontend environment variables must be prefixed with `VITE_`** to be accessible in the Vite build process.

2. **Environment variables are embedded at build time**, not runtime. You'll need to redeploy after changing environment variables.

3. **Preview deployments** (from pull requests) will use the same environment variables as production unless you configure them separately in Vercel project settings.

4. **Never commit sensitive keys** to the repository. Always use Vercel's environment variable settings.

## Backend CORS Configuration

After deploying to Vercel, update your backend's `CORS_ORIGINS` environment variable to include your Vercel domain:

```
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app,http://localhost:5173
```

Include:
- Your production Vercel domain
- Preview deployment domains (optional, if you want to test PRs)
- Local development URL (for local testing)

## Testing Environment Variables

You can verify environment variables are loaded correctly by checking the browser console or network tab. The `VITE_API_URL` should be used in API calls.

