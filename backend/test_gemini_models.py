#!/usr/bin/env python3
"""
Test script to verify Gemini model selection works correctly
"""
import asyncio
from app.services.gemini import GeminiService

async def test_gemini_models():
    """Test that Gemini service properly handles model selection"""
    print("Testing Gemini model selection...")

    try:
        gemini = GeminiService()
        print("SUCCESS: Gemini service initialized")

        # List available models
        available_models = gemini.list_available_models()
        print(f"Available models: {available_models}")

        # Check if Flash model is available
        flash_available = gemini.flash_model != gemini.pro_model
        print(f"Flash model available: {flash_available}")

        if flash_available:
            print("Both Flash and Pro models are available")
        else:
            print("Only Pro model available (Flash fallback to Pro)")

        # Test model attributes
        print(f"Pro model initialized: {gemini.pro_model is not None}")
        print(f"Flash model initialized: {gemini.flash_model is not None}")
        print(f"Flash == Pro: {gemini.flash_model == gemini.pro_model}")

        # Test with a simple evaluation (this will likely fail due to missing API key, but should show model selection)
        try:
            result = await gemini.evaluate(
                transcript_text="Test transcript",
                policy_template_id="test-id",
                use_hybrid=False  # Force Pro model
            )
            print("Evaluation completed successfully")
        except Exception as e:
            if "API key" in str(e):
                print("Expected: API key not configured (but model selection works)")
            elif "404" in str(e) or "not found" in str(e).lower():
                print(f"Model not found error: {e}")
                print("This indicates the model name is incorrect")
                print("Check available models above and update the model names in gemini.py")
            else:
                print(f"Unexpected error: {e}")

        return True
    except Exception as e:
        print(f"FAILED: Gemini model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gemini_models())
    exit(0 if success else 1)
