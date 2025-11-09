#!/usr/bin/env python3
"""
Script to start the uvicorn server with proper environment variables
"""
import os
import subprocess
import sys

def start_server():
    """Start the server with alignment disabled"""
    # Set environment variables
    env = os.environ.copy()
    env['ENABLE_ALIGNMENT'] = 'false'
    env['ALIGNMENT_TIMEOUT_SECONDS'] = '120'
    env['ALIGNMENT_MAX_DURATION_SECONDS'] = '180'

    print("🚀 Starting server with alignment DISABLED for faster processing...")
    print("📝 Environment variables set:")
    print("   ENABLE_ALIGNMENT=false")
    print("   ALIGNMENT_TIMEOUT_SECONDS=120")
    print("   ALIGNMENT_MAX_DURATION_SECONDS=180")
    print()

    try:
        # Start uvicorn with the environment variables
        cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(start_server())
