# GCP Storage Permissions Setup Guide

## Issue: 403 Permission Denied Error

If you're seeing errors like:
```
403 GET https://storage.googleapis.com/storage/v1/b/ai_qa_recording: 
ai-qa-backend@ai-qa-system.iam.gserviceaccount.com does not have storage.buckets.get access
```

This means your service account doesn't have the necessary permissions to access the Cloud Storage bucket.

## Solution: Grant Storage Permissions to Service Account

### Option 1: Using GCP Console (Recommended)

1. **Go to Cloud Storage Buckets:**
   - Navigate to [Google Cloud Console](https://console.cloud.google.com)
   - Select your project: `AI QA System`
   - Go to **Cloud Storage** > **Buckets**
   - Click on your bucket: `ai_qa_recording`

2. **Grant Bucket Permissions:**
   - Click on the **Permissions** tab
   - Click **Grant Access**
   - In the "New principals" field, enter your service account email:
     ```
     ai-qa-backend@ai-qa-system.iam.gserviceaccount.com
     ```
   - In the "Select a role" dropdown, choose one of:
     - **Storage Object Admin** (recommended) - Full control over objects in the bucket
     - **Storage Admin** - Full control over the bucket and objects
   - Click **Save**

### Option 2: Using IAM & Admin

1. **Go to IAM & Admin:**
   - Navigate to [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
   - Select your project: `AI QA System`

2. **Grant Service Account Role:**
   - Click **Grant Access**
   - In the "New principals" field, enter:
     ```
     ai-qa-backend@ai-qa-system.iam.gserviceaccount.com
     ```
   - In the "Select a role" dropdown, choose:
     - **Storage Object Admin** (for bucket-specific access)
     - **Storage Admin** (for project-wide storage access)
   - Click **Save**

### Option 3: Using gcloud CLI

If you have `gcloud` CLI installed:

```bash
# Grant Storage Object Admin role to the service account
gcloud projects add-iam-policy-binding ai-qa-system \
    --member="serviceAccount:ai-qa-backend@ai-qa-system.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# OR grant Storage Admin role (more permissions)
gcloud projects add-iam-policy-binding ai-qa-system \
    --member="serviceAccount:ai-qa-backend@ai-qa-system.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
```

### Option 4: Bucket-Level Permissions (More Restrictive)

If you want to grant permissions only to a specific bucket:

```bash
# Grant Storage Object Admin on specific bucket
gsutil iam ch serviceAccount:ai-qa-backend@ai-qa-system.iam.gserviceaccount.com:roles/storage.objectAdmin gs://ai_qa_recording
```

## Required Permissions

The service account needs at least these permissions:

- ✅ `storage.objects.create` - To upload files
- ✅ `storage.objects.get` - To read/download files
- ✅ `storage.objects.delete` - To delete files (optional)
- ✅ `storage.buckets.get` - To verify bucket exists (optional, but recommended)

The **Storage Object Admin** role includes all of these permissions.

## Verify Permissions

After granting permissions, verify they're working:

1. Restart your backend server
2. Try uploading a file through the API
3. Check the logs for any permission errors

## Troubleshooting

### Still Getting 403 Errors?

1. **Wait a few minutes** - IAM permission changes can take up to 5 minutes to propagate
2. **Check the service account email** - Ensure it matches exactly:
   ```
   ai-qa-backend@ai-qa-system.iam.gserviceaccount.com
   ```
3. **Verify the bucket name** - Ensure it matches:
   ```
   ai_qa_recording
   ```
4. **Check IAM conditions** - Make sure there are no IAM conditions blocking access
5. **Verify the project** - Ensure you're working in the correct GCP project

### Alternative: Use Different Service Account

If you continue to have issues, you can create a new service account with proper permissions:

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Name it (e.g., `storage-admin`)
4. Grant it the **Storage Object Admin** role
5. Create and download a new key
6. Update your `.env` file with the new service account credentials

## Security Best Practices

- ✅ Use **Storage Object Admin** instead of **Storage Admin** for least privilege
- ✅ Grant permissions at the bucket level when possible (not project-wide)
- ✅ Regularly audit service account permissions
- ✅ Use IAM conditions to restrict access by IP, time, etc. if needed

## Quick Reference

**Service Account Email:**
```
ai-qa-backend@ai-qa-system.iam.gserviceaccount.com
```

**Bucket Name:**
```
ai_qa_recording
```

**Recommended Role:**
```
Storage Object Admin (roles/storage.objectAdmin)
```

**Project ID:**
```
ai-qa-system
```

