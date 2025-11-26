"""
Check what phrases are actually configured in the database
"""

# These are the phrases I tested that worked:
my_tested_phrases = [
    # Stage 1 (Opening) - These WORKED in my test
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

print("=== WHAT I TESTED (that worked) ===")
for i, phrase in enumerate(my_tested_phrases, 1):
    print(f"{i:2d}. '{phrase}'")

print(f"\nTotal phrases tested: {len(my_tested_phrases)}")

print("\n=== WHAT'S ACTUALLY CONFIGURED ===")
print("Since I can't access the database directly, you need to check:")
print("1. Go to SOP Builder")
print("2. Check each step's 'Expected Phrases' field")
print("3. Compare with the list above")
print("4. If they don't match, update them to match realistic agent speech")

print("\n=== COMMON MISTAKES TO AVOID ===")
print("❌ 'Call recording disclosure required'")
print("✅ 'this call may be recorded'")
print()
print("❌ 'Agent must identify themselves'")
print("✅ 'my name is'")
print()
print("❌ 'Ask customer for issue details'")
print("✅ 'can you tell me more'")
print()
print("❌ 'Verify customer understanding'")
print("✅ 'does that make sense'")
