#!/usr/bin/env python3
"""
Script to configure CORS on GCP Storage bucket for direct browser uploads.

This allows the frontend to upload files directly to GCP Storage using signed URLs,
bypassing Cloud Run's 32MB request body limit.

Usage:
    python configure_gcp_storage_cors.py

Requirements:
    - GCP credentials configured (via environment variables or gcloud auth)
    - Storage Admin or Storage Bucket Admin role on the bucket
"""

import os
import sys
from google.cloud import storage
from google.oauth2 import service_account
from app.config import settings

def configure_cors():
    """Configure CORS on GCP Storage bucket"""
    
    print("🔧 Configuring CORS on GCP Storage bucket...")
    print(f"📦 Bucket: {settings.gcp_bucket_name}")
    print(f"🌐 Project: {settings.gcp_project_id}")
    print()
    
    # Create credentials
    credentials = None
    if settings.gcp_client_email and settings.gcp_private_key:
        private_key = settings.gcp_private_key.replace('\\n', '\n')
        credentials_info = {
            "type": "service_account",
            "project_id": settings.gcp_project_id,
            "private_key_id": "",
            "private_key": private_key,
            "client_email": settings.gcp_client_email,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.gcp_client_email.replace('@', '%40')}",
            "universe_domain": "googleapis.com"
        }
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        print(f"✅ Using service account: {settings.gcp_client_email}")
    else:
        print("⚠️  No service account credentials found, using default credentials")
        print("   Make sure you're authenticated with: gcloud auth application-default login")
    
    # Create storage client
    if credentials:
        client = storage.Client(credentials=credentials, project=settings.gcp_project_id)
    else:
        client = storage.Client(project=settings.gcp_project_id)
    
    # Get bucket
    try:
        bucket = client.bucket(settings.gcp_bucket_name)
        bucket.reload()
        print(f"✅ Connected to bucket: {settings.gcp_bucket_name}")
    except Exception as e:
        print(f"❌ Failed to access bucket: {e}")
        print(f"   Make sure the bucket exists and you have Storage Admin permissions")
        return 1
    
    # Define CORS configuration
    # Allow uploads from your frontend domains
    cors_config = [
        {
            "origin": ["https://www.qualitidex.com", "https://qualitidex.com", "http://localhost:5173"],
            "method": ["PUT", "POST", "GET", "HEAD", "DELETE"],
            "responseHeader": ["Content-Type", "Content-Length", "x-goog-resumable"],
            "maxAgeSeconds": 3600
        }
    ]
    
    # Update bucket CORS
    try:
        bucket.cors = cors_config
        bucket.patch()
        print()
        print("✅ CORS configuration updated successfully!")
        print()
        print("📋 CORS Configuration:")
        for rule in cors_config:
            print(f"   Origins: {', '.join(rule['origin'])}")
            print(f"   Methods: {', '.join(rule['method'])}")
            print(f"   Max Age: {rule['maxAgeSeconds']} seconds")
        print()
        print("🎉 Your bucket is now configured for direct browser uploads!")
        print("   Files larger than 32MB can now be uploaded using signed URLs.")
        return 0
    except Exception as e:
        print(f"❌ Failed to update CORS: {e}")
        print()
        print("💡 Alternative: Configure CORS manually in GCP Console:")
        print(f"   1. Go to: https://console.cloud.google.com/storage/browser/{settings.gcp_bucket_name}")
        print("   2. Click on the 'Configuration' tab")
        print("   3. Scroll to 'CORS configuration'")
        print("   4. Add the following JSON:")
        print()
        import json
        print(json.dumps(cors_config, indent=2))
        return 1

if __name__ == "__main__":
    try:
        exit_code = configure_cors()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)












