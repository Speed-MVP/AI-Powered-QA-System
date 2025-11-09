#!/usr/bin/env python3
"""
Test script to verify Gemini model initialization only
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import settings

# Set a dummy API key for testing if not set
if not settings.gemini_api_key:
    os.environ['GEMINI_API_KEY'] = 'dummy-key-for-testing'

try:
    import google.generativeai as genai

    # Configure with dummy key
    genai.configure(api_key='dummy-key-for-testing')

    print("Testing Gemini model availability...")

    # Test Pro models
    pro_models = ['gemini-pro-latest', 'gemini-2.5-pro', 'gemini-pro', 'gemini-1.5-pro']
    print("\nTesting Pro models:")
    working_pro = []
    for model_name in pro_models:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"  SUCCESS: {model_name} - Available")
            working_pro.append(model_name)
        except Exception as e:
            print(f"  FAILED: {model_name} - {str(e)[:50]}...")

    # Test Flash models
    flash_models = ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-flash', 'gemini-1.5-flash']
    print("\nTesting Flash models:")
    working_flash = []
    for model_name in flash_models:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"  SUCCESS: {model_name} - Available")
            working_flash.append(model_name)
        except Exception as e:
            print(f"  FAILED: {model_name} - {str(e)[:50]}...")

    print(f"\nRESULT: Found {len(working_pro)} working Pro models, {len(working_flash)} working Flash models")
    if working_pro:
        print(f"Use Pro model: {working_pro[0]}")
    if working_flash:
        print(f"Use Flash model: {working_flash[0]}")

except ImportError:
    print("FAILED: google-generativeai package not installed")
except Exception as e:
    print(f"FAILED: Error: {e}")
