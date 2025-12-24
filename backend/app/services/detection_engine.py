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
        
        logger.info(f"DETECTION_ENGINE: Starting detection for {len(behaviors)} behaviors across {len(agent_utterances)} agent utterances")
        
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
            
            logger.debug(f"DETECTION: Checking behavior '{behavior_name}' (id={behavior_id[:8]}..., mode={detection_mode}, "
                        f"phrases={len(phrases) if phrases else 0})")
            
            # Try to detect in agent utterances
            detection_result = None
            best_confidence = 0.0
            matched_text = None
            detection_time = None
            best_utterance_confidence = 0.0
            
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
                        best_utterance_confidence = deepgram_confidence
            
            # Evaluate compliance
            stage_start = None
            if agent_utterances:
                stage_start = agent_utterances[0].get("start") or 0
            
            compliance_result = self.compliance_evaluator.evaluate_behavior(
                behavior_type=behavior_type,
                detected=detection_result is not None,
                detection_time=detection_time,
                stage_start_time=stage_start,
                timing_constraints=timing_constraints,
                critical_action=critical_action
            )
            
            # Aggregate results
            behavior_result = self.aggregator.aggregate_behavior_detection(
                exact_result=detection_result if detection_result and detection_result.get("match_type") == "exact" else None,
                semantic_result=detection_result if detection_result and detection_result.get("match_type") == "semantic" else None,
                compliance_result=compliance_result,
                deepgram_confidence=best_utterance_confidence,
                utterance_count=len(agent_utterances)
            )
            
            behavior_result["behavior_id"] = behavior_id
            behavior_result["behavior_name"] = behavior_name
            behavior_result["start"] = detection_time
            end_time = detection_time + 2.0 if detection_time else None  # Estimate
            behavior_result["end"] = end_time
            
            # Log detection result
            detected = behavior_result.get("detected", False)
            confidence = behavior_result.get("confidence", 0.0)
            match_type = behavior_result.get("match_type", "none")
            if detected:
                logger.info(f"DETECTION_RESULT: '{behavior_name}' DETECTED (confidence={confidence:.2f}, type={match_type}, time={detection_time})")
            else:
                logger.debug(f"DETECTION_RESULT: '{behavior_name}' NOT detected")
            
            results["behaviors"].append(behavior_result)
        
        duration = time.time() - start_time
        
        # Calculate metrics
        detected_count = sum(1 for b in results["behaviors"] if b.get("detected", False))
        behaviors_count = len(results["behaviors"])
        avg_confidence = sum(b.get("confidence", 0) for b in results["behaviors"]) / behaviors_count if behaviors_count > 0 else 0
        
        # Log summary
        logger.info(f"DETECTION_SUMMARY: Detected {detected_count}/{behaviors_count} behaviors "
                   f"(avg_confidence={avg_confidence:.2f}, duration={duration:.2f}s)")
        
        # Log detected behavior names for easy debugging
        detected_names = [b.get("behavior_name") for b in results["behaviors"] if b.get("detected", False)]
        if detected_names:
            logger.info(f"DETECTION_SUMMARY: Detected behaviors: {', '.join(detected_names)}")
        
        not_detected_names = [b.get("behavior_name") for b in results["behaviors"] if not b.get("detected", False)]
        if not_detected_names:
            logger.debug(f"DETECTION_SUMMARY: Not detected: {', '.join(not_detected_names)}")
        
        # Record metrics (if blueprint_id available)
        # monitoring_service.record_detection_metric(...)
        
        return results

