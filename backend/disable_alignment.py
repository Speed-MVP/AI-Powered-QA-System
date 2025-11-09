#!/usr/bin/env python3
"""
Quick script to disable alignment for faster processing
Run this before starting the server to disable forced alignment
"""
import os

def disable_alignment():
    """Set environment variable to disable alignment"""
    os.environ['ENABLE_ALIGNMENT'] = 'false'
    print("✅ Alignment disabled for faster processing")
    print("📝 Forced alignment will be skipped for all audio files")
    print("🔄 Restart your server after running this script")
    print()
    print("To re-enable alignment later, run:")
    print("  set ENABLE_ALIGNMENT=true")
    print("  # or remove the environment variable")

if __name__ == "__main__":
    disable_alignment()
