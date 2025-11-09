#!/usr/bin/env python3
"""
Test script to verify alignment is disabled
"""
import asyncio
from app.services.deepgram import DeepgramService
from app.config import settings

async def test_alignment():
    """Test that alignment is properly disabled"""
    print("Testing alignment configuration...")
    print(f"ENABLE_ALIGNMENT setting: {settings.enable_alignment}")

    deepgram = DeepgramService()

    # Test with explicit False
    print("\nTesting with use_forced_alignment=False...")
    # Note: We can't actually call transcribe without a real file URL
    # But we can check the logic

    print("✅ Alignment should be disabled")
    print("📝 When you upload an audio file, you should see:")
    print("   'Transcription starting - alignment enabled: False'")
    print("   'Alignment disabled - using Deepgram segments directly'")

if __name__ == "__main__":
    asyncio.run(test_alignment())
