"""
Detection Engine - Phase 5
Main orchestrator for behavior detection
"""

import logging
from typing import List, Dict, Any, Optional
from app.services.detection.hybrid_detector import HybridDetector
from app.services.detection.compliance_evaluator import ComplianceEvaluator
from app.services.detection.aggregator import DetectionAggregator
from app.services.transcript_normalizer import TranscriptNormalizer
from app.services.embedding_service import EmbeddingService
from app.services.monitoring import monitoring_service
import time

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Main detection engine orchestrator"""
    
    def __init__(self, embedding_service=None):
        self.hybrid_detector = HybridDetector()
        self.compliance_evaluator = ComplianceEvaluator()
        self.aggregator = DetectionAggregator()
        self.normalizer = TranscriptNormalizer()
        self.embedding_service = embedding_service or EmbeddingService()
    
    def _normalize_utterance_text(self, text: Any) -> str:
        """
        Normalize individual utterance text.
        Handles cases where text might be a list, tuple, or other non-string type.
        
        Args:
            text: Text to normalize (can be str, list, tuple, etc.)
        
        Returns:
            Normalized string
        """
        # Handle list/tuple cases
        if isinstance(text, (list, tuple)):
            # Join list/tuple elements with spaces
            text = " ".join(str(item) for item in text)
        elif not isinstance(text, str):
            # Convert other types to string
            text = str(text) if text is not None else ""
        
        # Basic normalization: strip whitespace and clean up
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        return text.strip()
    
    def detect_behaviors(
        self,
        transcript_segments: List[Dict[str, Any]],
        behaviors: List[Dict[str, Any]],
        embedding_service = None
    ) -> Dict[str, Any]:
        """
        Detect all behaviors in transcript
        
        Args:
            transcript_segments: Diarized transcript segments with speaker labels
            behaviors: List of behaviors to detect (from compiled blueprint)
            embedding_service: Optional embedding service for semantic matching
        
        Returns:
            {
                "behaviors": [
                    {
                        "behavior_id": str,
                        "detected": bool,
                        "match_type": str,
                        "matched_text": str,
                        "confidence": float,
                        "violation": bool,
                        ...
                    }
                ],
                "stages": {
                    "stage_id": {
                        "deterministic_score": float,
                        "behaviors": [...]
                    }
                }
            }
        """
        start_time = time.time()
        
        results = {
            "behaviors": [],
            "stages": {}
        }
        
        # Filter agent utterances
        agent_utterances = [
            seg for seg in transcript_segments
            if seg.get("speaker") == "agent"
        ]
        
        # Detect each behavior
        for behavior in behaviors:
            behavior_id = behavior.get("id")
            behavior_name = behavior.get("name")
            behavior_type = behavior.get("metadata", {}).get("behavior_type", "required")
            detection_mode = behavior.get("detection_hint", "semantic")
            phrases = behavior.get("expected_phrases", [])
            description = behavior.get("description", behavior_name)
            critical_action = behavior.get("metadata", {}).get("critical_action")
            timing_constraints = behavior.get("metadata", {}).get("timing_requirement")
            
            # Try to detect in agent utterances
            detection_result = None
            best_confidence = 0.0
            matched_text = None
            detection_time = None
            
            for utterance in agent_utterances:
                utterance_text_raw = utterance.get("text", "")
                utterance_time = utterance.get("start", 0)
                deepgram_confidence = utterance.get("confidence", 1.0)
                
                # Normalize utterance text (handle list/tuple cases and do basic cleaning)
                normalized_text = self._normalize_utterance_text(utterance_text_raw)
                
                # Skip empty utterances
                if not normalized_text:
                    continue
                
                # Detect using hybrid detector
                match_result = self.hybrid_detector.detect(
                    utterance_text=normalized_text,
                    behavior_description=description,
                    behavior_phrases=phrases if phrases else None,
                    detection_mode=detection_mode,
                    embedding_service=embedding_service or self.embedding_service
                )
                
                if match_result and match_result.get("detected"):
                    confidence = match_result.get("confidence", 0.0)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        matched_text = match_result.get("matched_text", normalized_text)
                        detection_time = utterance_time
                        detection_result = match_result
            
            # Evaluate compliance
            compliance_result = self.compliance_evaluator.evaluate_behavior(
                behavior_type=behavior_type,
                detected=detection_result is not None,
                detection_time=detection_time,
                stage_start_time=agent_utterances[0].get("start", 0) if agent_utterances else None,
                timing_constraints=timing_constraints,
                critical_action=critical_action
            )
            
            # Aggregate results
            behavior_result = self.aggregator.aggregate_behavior_detection(
                exact_result=detection_result if detection_result and detection_result.get("match_type") == "exact" else None,
                semantic_result=detection_result if detection_result and detection_result.get("match_type") == "semantic" else None,
                compliance_result=compliance_result,
                deepgram_confidence=1.0,  # Would use actual from utterance
                utterance_count=len(agent_utterances)
            )
            
            behavior_result["behavior_id"] = behavior_id
            behavior_result["behavior_name"] = behavior_name
            behavior_result["start_time"] = detection_time
            behavior_result["end_time"] = detection_time + 2.0 if detection_time else None  # Estimate
            
            results["behaviors"].append(behavior_result)
        
        duration = time.time() - start_time
        
        # Calculate metrics
        detected_count = sum(1 for b in results["behaviors"] if b.get("detected", False))
        behaviors_count = len(results["behaviors"])
        avg_confidence = sum(b.get("confidence", 0) for b in results["behaviors"]) / behaviors_count if behaviors_count > 0 else 0
        
        # Record metrics (if blueprint_id available)
        # monitoring_service.record_detection_metric(...)
        
        return results

