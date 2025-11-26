"""
Test script to check if expected phrases match transcript content
"""

def normalize_text(text):
    """Normalize text for matching (same as in deterministic_rule_engine.py)"""
    if not text:
        return ""
    # Convert to lowercase, remove extra whitespace, normalize punctuation
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with spaces
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def test_phrase_matching():
    """Test if phrases match in transcript"""

    # Example transcript content (replace with actual transcript)
    transcript = """
    Hello thank you for calling ABC customer service. My name is Sarah Johnson and I'm calling from the technical support department. How can I help you today?

    I understand you're having issues with your internet connection. Let me check your account information. Can you please verify your account number for me?

    Thank you for providing that information. I can see the issue now. It looks like there's a service outage in your area. I'm going to escalate this to our network team.

    To summarize what I'll do: I'll have our network engineers look into this outage and get it resolved within the next 2 hours. You'll receive an email notification once it's fixed.

    Is there anything else I can help you with today? Thank you for your patience. Have a great day!
    """

    # Example expected phrases (replace with actual configured phrases)
    test_phrases = [
        "hello thank you for calling",
        "my name is",
        "how can i help you",
        "i understand",
        "can you please verify",
        "thank you for providing",
        "to summarize",
        "is there anything else",
        "have a great day"
    ]

    print("=== PHRASE MATCHING TEST ===")
    print(f"Transcript length: {len(transcript)} characters")
    print(f"Normalized transcript preview: {normalize_text(transcript)[:200]}...")
    print()

    matched_phrases = []
    unmatched_phrases = []

    for phrase in test_phrases:
        normalized_phrase = normalize_text(phrase)
        normalized_transcript = normalize_text(transcript)

        if normalized_phrase in normalized_transcript:
            matched_phrases.append(phrase)
            print(f"✅ MATCHED: '{phrase}'")
            # Find the context
            start = normalized_transcript.find(normalized_phrase)
            if start >= 0:
                context_start = max(0, start - 50)
                context_end = min(len(normalized_transcript), start + len(normalized_phrase) + 50)
                context = normalized_transcript[context_start:context_end]
                print(f"   Context: ...{context}...")
        else:
            unmatched_phrases.append(phrase)
            print(f"❌ NO MATCH: '{phrase}'")

    print()
    print("=== SUMMARY ===")
    print(f"Matched: {len(matched_phrases)}/{len(test_phrases)}")
    print(f"Unmatched: {len(unmatched_phrases)}")

    if unmatched_phrases:
        print("\nUnmatched phrases:")
        for phrase in unmatched_phrases:
            print(f"  - '{phrase}'")

if __name__ == "__main__":
    test_phrase_matching()
