#!/usr/bin/env python3
"""
Test script to verify Gemini service handles sentiment analysis correctly
"""
import asyncio
from app.services.gemini import GeminiService

async def test_gemini_sentiment():
    """Test the Gemini service with mock sentiment analysis data"""
    print("Testing Gemini service sentiment analysis...")

    # Mock sentiment analysis data (Deepgram format)
    mock_sentiment = [
        {
            "speaker": "caller",
            "sentiment": {"sentiment": "negative", "confidence": 0.85},
            "start": 10.0,
            "end": 15.0,
            "text": "This is unacceptable!"
        },
        {
            "speaker": "agent",
            "sentiment": {"sentiment": "neutral", "confidence": 0.72},
            "start": 16.0,
            "end": 25.0,
            "text": "I understand your frustration and will help resolve this."
        }
    ]

    # Test the sentiment formatting
    gemini = GeminiService()
    try:
        formatted = gemini._format_sentiment_analysis(mock_sentiment)
        print("SUCCESS: Gemini sentiment formatting works!")
        print("Formatted length:", len(formatted))
        print("Contains CALLER:", "CALLER" in formatted)
        print("Contains AGENT:", "AGENT" in formatted)

        # Test complexity assessment
        complexity = gemini._assess_call_complexity("test transcript", mock_sentiment, None)
        print("SUCCESS: Complexity assessment works!")
        print("Complexity score:", complexity)

        return True
    except Exception as e:
        print(f"FAILED: Gemini sentiment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gemini_sentiment())
    exit(0 if success else 1)
