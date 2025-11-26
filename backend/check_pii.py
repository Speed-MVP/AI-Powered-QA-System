import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pii_redactor import PIIRedactor

def check_pii():
    redactor = PIIRedactor()
    text = "Good morning. Thank you for calling ACME support. My name is Sarah."
    redacted = redactor.redact_text(text)
    print(f"Original: {text}")
    print(f"Redacted: {redacted}")

if __name__ == "__main__":
    check_pii()
