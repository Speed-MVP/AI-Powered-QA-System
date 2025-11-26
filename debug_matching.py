"""
Debug script to test your actual configured phrases against transcript
"""

def normalize_text(text):
    """Normalize text for matching (same as in deterministic_rule_engine.py)"""
    if not text:
        return ""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with spaces
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def debug_phrase_matching():
    """Test your actual phrases against your transcript"""

    # YOUR ACTUAL TRANSCRIPT
    transcript = """
Good morning. Thank you for calling ACME support. Before we proceed, this call may be recorded for quality and training purposes. My name is Sarah. May I have your full name or the email on your account I can verify your identity?

Sure. It's John Martinez. Email is john dot sample dot com.

Thank you, John. I verify your account. How can I assist you today?

I'm having trouble logging in.

I understand, John. Can you tell me more about the issue? When did the problem start? Take take your time. I'm here to help.

It started an hour ago. I kept getting an error.

Got it. Thanks for explaining that. just to confirm, you're entering your username and password, and the system returns an error every time. Correct?

Yes. That's right.

No worries, Jen. Let's fix this together. First, on your screen, you should see the login button. Please click it once, then clear your brochure cache using the shortcut control plus shift plus delete.

. Doing it now.

Great. Go ahead and try logging it again.

Yes. It worked.

Perfect. Glad to hear that. Is everything working as expected now? Any other issues I can assist you with?

No. That fixed it.

Great. To summarize, the login error was caused by cache browser data, and clearing the cache resolved the issue completely. Your session should remain stable moving forward. Before we end, is there anything else I can help you with today?

No. That's all.

. Thank you for calling ACME support. Have a great day, John.
    """

    # WHAT SHOULD BE CONFIGURED (based on default template + transcript)
    configured_phrases = [
        # Stage 1 (Opening) - These WORK in evaluation!
        "this call may be recorded",
        "my name is",
        "may i have your full name",

        # Stage 2 (Discovery) - These should work but DON'T
        "how can i assist you",
        "i understand",
        "can you tell me more",
        "when did the problem start",
        "take your time",
        "just to confirm",
        "you're entering your username",

        # Stage 3 (Resolution) - These should work but DON'T
        "let's fix this together",
        "clear your browser cache",
        "control plus shift plus delete",
        "go ahead and try",
        "glad to hear that",
        "is everything working",

        # Stage 4 (Closing) - These should work but DON'T
        "to summarize",
        "the login error was caused",
        "clearing the cache resolved",
        "is there anything else i can help",
        "thank you for calling",
        "have a great day"
    ]

    if "[PASTE YOUR FULL TRANSCRIPT HERE" in transcript:
        print("❌ ERROR: You need to paste your actual transcript content!")
        return

    if not configured_phrases or "hello" in configured_phrases[0]:
        print("❌ ERROR: You need to paste your actual configured phrases!")
        return

    print("=== DEBUGGING PHRASE MATCHING ===")
    print(f"Transcript length: {len(transcript)} characters")
    print(f"Configured phrases: {len(configured_phrases)}")
    print()

    matched_phrases = []
    unmatched_phrases = []

    for phrase in configured_phrases:
        normalized_phrase = normalize_text(phrase)
        normalized_transcript = normalize_text(transcript)

        if normalized_phrase in normalized_transcript:
            matched_phrases.append(phrase)
            print(f"✅ MATCHED: '{phrase}'")
        else:
            unmatched_phrases.append(phrase)
            print(f"❌ NO MATCH: '{phrase}'")
            # Suggest alternatives
            print(f"   💡 Try variations like: '{phrase.lower()}', '{phrase.replace('i ', 'I ')}'")

    print()
    print("=== RESULTS ===")
    print(f"✅ Matched: {len(matched_phrases)}/{len(configured_phrases)}")
    print(f"❌ Unmatched: {len(unmatched_phrases)}")

    if unmatched_phrases:
        print("\n🔧 FIXES NEEDED:")
        print("1. Check if your phrases are too specific")
        print("2. Try shorter, more common variations")
        print("3. Make sure phrases match actual agent speech patterns")
        print("4. Consider ASR errors (e.g., 'brochure' → 'browser')")

if __name__ == "__main__":
    debug_phrase_matching()
