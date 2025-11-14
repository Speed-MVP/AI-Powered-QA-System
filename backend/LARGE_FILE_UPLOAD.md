# Large File Upload Configuration

## Issue: 413 Content Too Large Error

If you're experiencing `413 (Content Too Large)` errors when uploading files, this is likely due to Cloud Run's 32MB request body size limit.

## Solutions

### Option 1: Configure CORS on GCP Storage Bucket (Recommended for Large Files)

To enable direct browser uploads to GCP Storage (bypassing Cloud Run's 32MB limit):

1. **Run the configuration script:**
   ```bash
   cd backend
   python configure_gcp_storage_cors.py
   ```

2. **Or configure manually in GCP Console:**
   - Go to [GCP Storage Console](https://console.cloud.google.com/storage/browser)
   - Select your bucket
   - Click "Configuration" tab
   - Scroll to "CORS configuration"
   - Add this configuration:
   ```json
   [
     {
       "origin": ["https://www.qualitidex.com", "https://qualitidex.com", "http://localhost:5173"],
       "method": ["PUT", "POST", "GET", "HEAD", "DELETE"],
       "responseHeader": ["Content-Type", "Content-Length", "x-goog-resumable"],
       "maxAgeSeconds": 3600
     }
   ]
   ```

3. **After configuring CORS**, the frontend will automatically use signed URL uploads for files > 30MB.

### Option 2: Increase Cloud Run Request Size Limit

Cloud Run has a default 32MB limit. To increase it:

1. Go to Cloud Run Console
2. Edit your service
3. Under "Container", set "Request timeout" to a higher value (e.g., 300s)
4. Note: The 32MB body size limit is hardcoded in Cloud Run and cannot be changed directly

### Option 3: Use Streaming Upload (Current Implementation)

The current implementation uses streaming upload which reads files in 8KB chunks. This helps with memory usage but still has the 32MB Cloud Run limit.

## Configuration

The backend is configured to:
- Stream file uploads in 8KB chunks
- Use temporary files for large uploads
- Log large file uploads (>100MB)

## Testing

To test large file uploads:
1. Try uploading a file < 32MB - should work
2. Try uploading a file > 32MB - will get 413 error
3. For files > 32MB, use the signed URL method

## Future Improvements

Consider implementing:
- Automatic fallback to signed URL for large files
- Client-side file size checking before upload
- Progress indicators for large uploads

