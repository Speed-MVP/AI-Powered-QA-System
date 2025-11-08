"""
Test script to verify GCP credentials and bucket access
Run this to diagnose credential issues: python test_gcp_credentials.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google.cloud import storage
from google.oauth2 import service_account
from google.api_core import exceptions

def test_credentials():
    """Test GCP credentials and bucket access"""
    
    # Get credentials from environment
    gcp_client_email = os.getenv('GCP_CLIENT_EMAIL')
    gcp_private_key = os.getenv('GCP_PRIVATE_KEY')
    gcp_project_id = os.getenv('GCP_PROJECT_ID')
    gcp_bucket_name = os.getenv('GCP_BUCKET_NAME')
    
    print("=" * 60)
    print("GCP Credentials Test")
    print("=" * 60)
    
    # Check environment variables
    print(f"\n1. Environment Variables:")
    print(f"   GCP_PROJECT_ID: {gcp_project_id}")
    print(f"   GCP_BUCKET_NAME: {gcp_bucket_name}")
    print(f"   GCP_CLIENT_EMAIL: {gcp_client_email}")
    print(f"   GCP_PRIVATE_KEY: {'Set' if gcp_private_key else 'Not set'} ({len(gcp_private_key) if gcp_private_key else 0} chars)")
    
    if not all([gcp_client_email, gcp_private_key, gcp_project_id, gcp_bucket_name]):
        print("\n❌ ERROR: Missing required environment variables!")
        return False
    
    # Create credentials
    print(f"\n2. Creating Service Account Credentials...")
    try:
        private_key = gcp_private_key.replace('\\n', '\n')
        credentials_info = {
            "type": "service_account",
            "project_id": gcp_project_id,
            "private_key_id": "",
            "private_key": private_key,
            "client_email": gcp_client_email,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{gcp_client_email.replace('@', '%40')}",
            "universe_domain": "googleapis.com"
        }
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        print(f"   ✅ Credentials created successfully")
        print(f"   Service Account: {credentials.service_account_email}")
    except Exception as e:
        print(f"   ❌ ERROR creating credentials: {e}")
        return False
    
    # Create storage client
    print(f"\n3. Creating Storage Client...")
    try:
        client = storage.Client(credentials=credentials, project=gcp_project_id)
        print(f"   ✅ Storage client created successfully")
    except Exception as e:
        print(f"   ❌ ERROR creating storage client: {e}")
        return False
    
    # Test bucket access
    print(f"\n4. Testing Bucket Access: {gcp_bucket_name}")
    try:
        bucket = client.bucket(gcp_bucket_name)
        
        # Try to get bucket metadata
        print(f"   Attempting to get bucket metadata...")
        try:
            bucket.reload()
            print(f"   ✅ Successfully accessed bucket metadata")
            print(f"   Bucket Location: {bucket.location}")
            print(f"   Bucket Storage Class: {bucket.storage_class}")
        except exceptions.Forbidden as e:
            print(f"   ⚠️  WARNING: Cannot access bucket metadata (403 Forbidden)")
            print(f"   This is okay if you only have object-level permissions")
            print(f"   Error: {e}")
        except Exception as e:
            print(f"   ❌ ERROR accessing bucket: {e}")
            return False
        
        # Try to list objects (tests object permissions)
        print(f"\n5. Testing Object Permissions...")
        try:
            blobs = list(client.list_blobs(bucket, max_results=1))
            print(f"   ✅ Successfully listed objects (have object read permission)")
        except exceptions.Forbidden as e:
            print(f"   ❌ ERROR: Cannot list objects (403 Forbidden)")
            print(f"   Service account needs 'Storage Object Viewer' or higher")
            print(f"   Error: {e}")
            return False
        except Exception as e:
            print(f"   ⚠️  WARNING: Could not list objects: {e}")
        
        # Try to create a test blob (tests object write permission)
        print(f"\n6. Testing Write Permissions...")
        try:
            test_blob = bucket.blob("_test_write_permission.txt")
            test_blob.upload_from_string("test", content_type="text/plain")
            print(f"   ✅ Successfully uploaded test file (have object write permission)")
            # Clean up
            test_blob.delete()
            print(f"   ✅ Successfully deleted test file")
        except exceptions.Forbidden as e:
            print(f"   ❌ ERROR: Cannot write objects (403 Forbidden)")
            print(f"   Service account needs 'Storage Object Creator' or higher")
            print(f"   Error: {e}")
            return False
        except Exception as e:
            print(f"   ❌ ERROR testing write: {e}")
            return False
        
        print(f"\n" + "=" * 60)
        print("✅ All tests passed! Credentials are working correctly.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_credentials()
    sys.exit(0 if success else 1)

