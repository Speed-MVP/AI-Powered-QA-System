# Troubleshooting Cloud Run Deployment

## Error: Container failed to start and listen on PORT

This error means the container didn't start the server within the timeout period.

### Common Causes:

1. **Missing Environment Variables**
   - `DATABASE_URL` not set
   - `GCP_PROJECT_ID` not set
   - Other required variables missing

2. **Database Connection Failed**
   - Database URL incorrect
   - Database not accessible from Cloud Run
   - Database credentials wrong

3. **Migrations Failed**
   - Database connection error
   - Migration scripts have errors

4. **Application Startup Error**
   - Import errors
   - Configuration errors
   - Missing dependencies

## How to Fix

### Step 1: Check Cloud Run Logs

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service: `ai-qa-system`
3. Click **"Logs"** tab
4. Look for error messages

### Step 2: Verify Environment Variables

In Cloud Run service settings:

1. Go to your service
2. Click **"Edit & Deploy New Revision"**
3. Go to **"Variables & Secrets"** tab
4. Verify these are set:
   - ✅ `DATABASE_URL` - Your PostgreSQL connection string
   - ✅ `GCP_PROJECT_ID` - Your GCP project ID
   - ✅ `GCP_BUCKET_NAME` - Your GCP Storage bucket name
   - ✅ `JWT_SECRET` - Your JWT secret key
   - ✅ `DEEPGRAM_API_KEY` - Your Deepgram API key
   - ✅ `GEMINI_API_KEY` - Your Gemini API key
   - ✅ `CORS_ORIGINS` - Allowed CORS origins
   - ✅ `ENVIRONMENT` - Set to `production`
   - ✅ `LOG_LEVEL` - Set to `INFO`

### Step 3: Check Database Connectivity

#### For Neon Database:

1. Make sure your database allows connections from Cloud Run
2. Check if your database URL is correct:
   ```
   postgresql://user:password@host.neon.tech/dbname?sslmode=require
   ```
3. Verify the database is running and accessible

#### Test Database Connection:

You can test the database connection by checking the logs. If you see:
```
OperationalError: could not connect to server
```
Then the database is not accessible.

**Solution:**
- Check database firewall settings
- Verify database URL is correct
- Ensure database allows connections from Cloud Run IPs (0.0.0.0/0 for public databases)

### Step 4: Make Migrations Optional (Temporary Fix)

The Dockerfile now continues even if migrations fail. However, you should still fix the database connection.

### Step 5: Increase Startup Timeout

1. Go to Cloud Run service
2. Click **"Edit & Deploy New Revision"**
3. Go to **"Container"** tab
4. Expand **"Advanced settings"**
5. Increase **"Startup timeout"** to `300s` (5 minutes)
6. Click **"Deploy"**

### Step 6: Check Container Port

1. Go to Cloud Run service settings
2. Verify **Container port** is set to `8080`
3. The application listens on the PORT environment variable (defaults to 8080)

## Quick Fix Checklist

- [ ] All environment variables are set in Cloud Run
- [ ] DATABASE_URL is correct and accessible
- [ ] Database allows connections from Cloud Run
- [ ] Container port is set to 8080
- [ ] Startup timeout is at least 240s
- [ ] Check logs for specific error messages
- [ ] Verify GCP_PROJECT_ID is correct
- [ ] Verify GCP_BUCKET_NAME exists and is accessible

## Testing Locally First

Before deploying to Cloud Run, test locally:

```bash
# Set environment variables
export DATABASE_URL="your-database-url"
export GCP_PROJECT_ID="your-project-id"
# ... other variables

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

If it works locally but not in Cloud Run, the issue is likely:
- Environment variables not set in Cloud Run
- Database not accessible from Cloud Run
- GCP permissions issue

## Common Error Messages

### "OperationalError: could not connect to server"
- **Cause**: Database not accessible
- **Fix**: Check database URL, firewall settings, and network connectivity

### "KeyError: 'DATABASE_URL'"
- **Cause**: Environment variable not set
- **Fix**: Set DATABASE_URL in Cloud Run environment variables

### "Bucket not found"
- **Cause**: GCP_BUCKET_NAME incorrect or bucket doesn't exist
- **Fix**: Verify bucket name and ensure service account has access

### "Permission denied"
- **Cause**: Service account doesn't have required permissions
- **Fix**: Grant Storage Admin role to Cloud Run service account

## Getting Help

1. Check Cloud Run logs for detailed error messages
2. Check Cloud Build logs if build fails
3. Verify all environment variables are set
4. Test database connection separately
5. Review the deployment logs URL provided in the error

## Next Steps After Fix

Once the container starts successfully:

1. Check the service URL
2. Test the `/health` endpoint
3. Test the `/docs` endpoint (Swagger UI)
4. Update Vercel with the API URL
5. Update CORS settings with your Vercel domain

