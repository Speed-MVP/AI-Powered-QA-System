# Environment Variables for Cloud Run

## Required Environment Variables

You MUST set these in Cloud Run for the application to start:

### Database
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```
Your PostgreSQL database connection string (e.g., from Neon, Supabase, or Cloud SQL)

### GCP Configuration
```
GCP_PROJECT_ID=your-project-id
GCP_BUCKET_NAME=your-bucket-name
```
Your Google Cloud Project ID and Storage bucket name

### Authentication
```
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters-long
```
A secure random string for JWT token signing (minimum 32 characters)

### API Keys
```
DEEPGRAM_API_KEY=your-deepgram-api-key
GEMINI_API_KEY=your-gemini-api-key
```
Your Deepgram and Gemini API keys

### Email Configuration
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
```
SMTP settings for email notifications

### Server Configuration
```
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
```
- `ENVIRONMENT`: Set to `production`
- `LOG_LEVEL`: Set to `INFO` or `DEBUG` for more logs
- `CORS_ORIGINS`: Comma-separated list of allowed frontend URLs

## How to Set Environment Variables in Cloud Run

### Method 1: During Initial Deployment

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. After configuring container image, go to **"Variables & Secrets"** tab
4. Click **"Add Variable"** for each environment variable
5. Enter the variable name and value
6. Click **"Create"** to deploy

### Method 2: Update Existing Service

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service: `ai-qa-system`
3. Click **"Edit & Deploy New Revision"**
4. Go to **"Variables & Secrets"** tab
5. Click **"Add Variable"** or edit existing variables
6. Enter variable name and value
7. Click **"Deploy"**

### Method 3: Using Secret Manager (Recommended for Production)

For sensitive values like API keys and passwords:

1. Go to [Secret Manager](https://console.cloud.google.com/security/secret-manager)
2. Create a secret for each sensitive value
3. In Cloud Run, go to **"Variables & Secrets"** tab
4. Click **"Add Secret"**
5. Select the secret and choose how to expose it (as environment variable)
6. Deploy the revision

## Environment Variable Format

### DATABASE_URL Examples

**Neon PostgreSQL:**
```
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
```

**Cloud SQL:**
```
DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/project:region:instance
```

**Standard PostgreSQL:**
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### CORS_ORIGINS Examples

**Single frontend:**
```
CORS_ORIGINS=https://your-app.vercel.app
```

**Multiple frontends (including www and non-www variants):**
```
CORS_ORIGINS=https://qualitidex.com,https://www.qualitidex.com,http://localhost:5173
```

**Important**: 
- Include both `www` and non-`www` versions of your domain (e.g., `https://qualitidex.com` AND `https://www.qualitidex.com`)
- No spaces after commas
- The backend will automatically add variations, but it's best to explicitly include all domains you use
- If you get CORS errors, check that your frontend's exact origin URL is in this list

## Verification

After setting environment variables:

1. Check Cloud Run logs to verify variables are loaded
2. Look for any "WARNING: ... not set" messages
3. Test the `/health` endpoint
4. Check application logs for configuration errors

## Troubleshooting

### "ValidationError: field required"

This means a required environment variable is missing. Check:
- All required variables are set in Cloud Run
- Variable names are correct (case-sensitive)
- No typos in variable names

### "OperationalError: could not connect to server"

- Check DATABASE_URL is correct
- Verify database is accessible from Cloud Run
- Check database firewall/network settings

### "Bucket not found"

- Verify GCP_BUCKET_NAME is correct
- Check bucket exists in your GCP project
- Verify service account has access to the bucket

## Quick Checklist

Before deploying, ensure you have:

- [ ] DATABASE_URL (PostgreSQL connection string)
- [ ] GCP_PROJECT_ID (your GCP project ID)
- [ ] GCP_BUCKET_NAME (your Storage bucket name)
- [ ] JWT_SECRET (random secure string, 32+ characters)
- [ ] DEEPGRAM_API_KEY (from Deepgram dashboard)
- [ ] GEMINI_API_KEY (from Google AI Studio)
- [ ] SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
- [ ] ENVIRONMENT=production
- [ ] LOG_LEVEL=INFO
- [ ] CORS_ORIGINS (your frontend URLs)

## Security Notes

1. **Never commit environment variables** to Git
2. **Use Secret Manager** for production secrets
3. **Rotate secrets regularly** (especially JWT_SECRET and API keys)
4. **Use different values** for development and production
5. **Restrict CORS_ORIGINS** to your actual frontend URLs only

