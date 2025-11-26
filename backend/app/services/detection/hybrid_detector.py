"""
Hybrid Decision Logic - Phase 5
Combines exact + semantic matching
"""

import logging
from typing import Dict, Any, Optional
from .exact_matcher import ExactMatcher
from .semantic_matcher import SemanticMatcher

logger = logging.getLogger(__name__)


class HybridDetector:
    """Hybrid detection combining exact and semantic"""
    
    def __init__(self):
        self.exact_matcher = ExactMatcher()
        self.semantic_matcher = SemanticMatcher()
    
    def detect(
        self,
        utterance_text: str,
        behavior_description: str,
        behavior_phrases: Optional[list] = None,
        detection_mode: str = "hybrid",
        embedding_service = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect behavior using hybrid logic
        
        Args:
            utterance_text: Agent utterance
            behavior_description: Behavior description
            behavior_phrases: Optional phrases list
            detection_mode: "semantic", "exact_phrase", or "hybrid"
            embedding_service: Embedding service for semantic matching
        
        Returns:
            Detection result or None
        """
        if detection_mode == "semantic":
            return self.semantic_matcher.match(
                utterance_text,
                behavior_description,
                behavior_phrases,
                embedding_service
            )
        
        elif detection_mode == "exact_phrase":
            if not behavior_phrases:
                return None
            return self.exact_matcher.match(
                utterance_text,
                behavior_phrases,
                "exact"
            )
        
        elif detection_mode == "hybrid":
            # Try exact first
            if behavior_phrases:
                exact_result = self.exact_matcher.match(
                    utterance_text,
                    behavior_phrases,
                    "fuzzy"  # Use fuzzy for hybrid
                )
                if exact_result:
                    return exact_result
            
            # Fall back to semantic
            semantic_result = self.semantic_matcher.match(
                utterance_text,
                behavior_description,
                behavior_phrases,
                embedding_service
            )
            return semantic_result
        
        return None

