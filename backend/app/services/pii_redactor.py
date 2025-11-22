"""
Phase 4: PII Redaction Service
Redacts personally identifiable information from transcripts before sending to LLM.
Per DATA_PRIVACY_AND_LLM_USAGE.md requirements.
"""

import re
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class PIIRedactor:
    """
    Redacts PII from transcripts per DATA_PRIVACY_AND_LLM_USAGE.md spec.
    """
    
    def __init__(self):
        # Compile regex patterns for PII detection
        self.patterns = {
            "name": re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', re.IGNORECASE),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            "account_number": re.compile(r'\b(?:account|acct|acc)[\s#:]*(\d{4,})\b', re.IGNORECASE),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "address": re.compile(r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b', re.IGNORECASE),
            "order_id": re.compile(r'\b(?:order|ord|ref|reference)[\s#:]*([A-Z0-9]{6,})\b', re.IGNORECASE),
        }
    
    def redact_text(self, text: str) -> str:
        """
        Redact PII from text string.
        Returns redacted text with placeholders.
        """
        if not text:
            return text
        
        redacted = text
        
        # Redact names (common patterns)
        redacted = self.patterns["name"].sub("{{NAME}}", redacted)
        
        # Redact emails
        redacted = self.patterns["email"].sub("{{EMAIL}}", redacted)
        
        # Redact phone numbers
        redacted = self.patterns["phone"].sub("{{PHONE}}", redacted)
        
        # Redact credit card numbers
        redacted = self.patterns["credit_card"].sub("{{CARD_NUMBER}}", redacted)
        
        # Redact account numbers
        redacted = self.patterns["account_number"].sub(r"{{ACCOUNT_NUMBER}}", redacted)
        
        # Redact SSN
        redacted = self.patterns["ssn"].sub("{{GOV_ID}}", redacted)
        
        # Redact addresses
        redacted = self.patterns["address"].sub("{{ADDRESS}}", redacted)
        
        # Redact order IDs
        redacted = self.patterns["order_id"].sub(r"{{ORDER_ID}}", redacted)
        
        return redacted
    
    def redact_segments(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Redact PII from transcript segments.
        Preserves speaker attribution and timestamps.
        """
        redacted_segments = []
        
        for segment in segments:
            redacted_segment = segment.copy()
            text = segment.get("text", "")
            redacted_text = self.redact_text(text)
            redacted_segment["text"] = redacted_text
            redacted_segments.append(redacted_segment)
        
        return redacted_segments
    
    def redact_transcript(
        self,
        transcript_text: str,
        segments: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Redact PII from both transcript text and segments.
        Returns (redacted_text, redacted_segments)
        """
        redacted_text = self.redact_text(transcript_text)
        redacted_segments = self.redact_segments(segments)
        
        return redacted_text, redacted_segments

