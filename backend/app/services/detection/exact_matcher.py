"""
Exact Match Engine - Phase 5
Literal, fuzzy, and phonetic matching for behaviors
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ExactMatcher:
    """Exact phrase matching with fuzzy and phonetic support"""
    
    def __init__(self, fuzzy_threshold: float = 0.85, levenshtein_threshold: float = 0.15):
        self.fuzzy_threshold = fuzzy_threshold
        self.levenshtein_threshold = levenshtein_threshold
    
    def match(
        self,
        text: str,
        phrases: List[str],
        match_type: str = "exact"
    ) -> Optional[Dict[str, Any]]:
        """
        Match text against phrases
        
        Args:
            text: Text to search in
            phrases: List of phrases to match
            match_type: "exact", "fuzzy", or "phonetic"
        
        Returns:
            Match result with confidence and matched text, or None
        """
        # Handle cases where text might be a tuple, list, or other non-string type
        if isinstance(text, (list, tuple)):
            # Join list/tuple elements with spaces
            text = " ".join(str(item) for item in text)
        elif not isinstance(text, str):
            # Convert other types to string
            text = str(text) if text is not None else ""
        
        # Return None if text is empty after conversion
        if not text:
            return None
        
        text_lower = text.lower()
        
        for phrase in phrases:
            phrase_lower = phrase.lower()
            
            # 1. Literal substring match
            if phrase_lower in text_lower:
                return {
                    "detected": True,
                    "match_type": "exact",
                    "confidence": 1.0,
                    "matched_text": self._extract_match_context(text, phrase),
                    "matched_phrase": phrase
                }
            
            # 2. Fuzzy match (if enabled)
            if match_type in ["fuzzy", "hybrid"]:
                similarity = self._fuzzy_similarity(text_lower, phrase_lower)
                if similarity >= self.fuzzy_threshold:
                    return {
                        "detected": True,
                        "match_type": "fuzzy",
                        "confidence": similarity,
                        "matched_text": self._extract_match_context(text, phrase),
                        "matched_phrase": phrase
                    }
            
            # 3. Phonetic match (optional, simplified)
            if match_type == "phonetic":
                if self._phonetic_match(text_lower, phrase_lower):
                    return {
                        "detected": True,
                        "match_type": "phonetic",
                        "confidence": 0.8,  # Lower confidence for phonetic
                        "matched_text": self._extract_match_context(text, phrase),
                        "matched_phrase": phrase
                    }
        
        return None
    
    def _fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Calculate fuzzy similarity using SequenceMatcher"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _phonetic_match(self, text1: str, text2: str) -> bool:
        """
        Simplified phonetic matching
        In production, would use Soundex or Metaphone
        """
        # Simple approach: check if key sounds match
        # Remove vowels and compare consonants
        def simplify(text):
            return re.sub(r'[aeiou\s]', '', text.lower())
        
        return simplify(text1) == simplify(text2)
    
    def _extract_match_context(self, text: str, phrase: str, context_chars: int = 50) -> str:
        """Extract context around matched phrase"""
        text_lower = text.lower()
        phrase_lower = phrase.lower()
        
        idx = text_lower.find(phrase_lower)
        if idx == -1:
            return text[:context_chars] if len(text) > context_chars else text
        
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(phrase) + context_chars)
        
        return text[start:end]

