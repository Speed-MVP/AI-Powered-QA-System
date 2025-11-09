#!/usr/bin/env python3
"""
Test script to verify rule engine works with sentiment analysis
"""
import asyncio
from app.services.rule_engine import RuleEngineService

def test_rule_engine():
    """Test the rule engine with mock sentiment analysis data"""
    print("Testing rule engine with sentiment analysis...")

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

    # Mock transcript segments
    mock_segments = [
        {
            "speaker": "caller",
            "text": "This is unacceptable!",
            "start": 10.0,
            "end": 15.0
        },
        {
            "speaker": "agent",
            "text": "I understand your frustration and will help resolve this.",
            "start": 16.0,
            "end": 25.0
        }
    ]

    # Test rule engine
    rule_engine = RuleEngineService()
    try:
        results = rule_engine.evaluate_rules(
            transcript_segments=mock_segments,
            sentiment_analysis=mock_sentiment
        )
        print("SUCCESS: Rule engine test passed!")
        print(f"   Found {len(results.get('violations', []))} violations")
        print(f"   Rule scores: {list(results.get('rule_scores', {}).keys())}")
        return True
    except Exception as e:
        print(f"FAILED: Rule engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rule_engine()
    exit(0 if success else 1)
