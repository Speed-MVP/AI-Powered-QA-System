"""
Rule Compliance Evaluator - Phase 5
Evaluates required/forbidden/critical behaviors and timing constraints
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ComplianceEvaluator:
    """Evaluates compliance rules for behaviors"""
    
    def evaluate_behavior(
        self,
        behavior_type: str,
        detected: bool,
        detection_time: Optional[float] = None,
        stage_start_time: Optional[float] = None,
        timing_constraints: Optional[Dict[str, Any]] = None,
        critical_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate behavior compliance
        
        Returns:
            {
                "violation": bool,
                "violation_reason": str or None,
                "timing_passed": bool,
                "critical_violation": bool
            }
        """
        result = {
            "violation": False,
            "violation_reason": None,
            "timing_passed": True,
            "critical_violation": False
        }
        
        # Check required behaviors
        if behavior_type == "required":
            if not detected:
                result["violation"] = True
                result["violation_reason"] = "required_action_missing"
        
        # Check forbidden behaviors
        elif behavior_type == "forbidden":
            if detected:
                result["violation"] = True
                result["violation_reason"] = "forbidden_phrase_used"
        
        # Check critical behaviors
        elif behavior_type == "critical":
            if not detected and behavior_type == "required":
                result["violation"] = True
                result["violation_reason"] = "critical_action_missing"
                result["critical_violation"] = True
            elif detected and behavior_type == "forbidden":
                result["violation"] = True
                result["violation_reason"] = "critical_forbidden_phrase_used"
                result["critical_violation"] = True
        
        # Check timing constraints
        if timing_constraints and detection_time and stage_start_time:
            expected_seconds = timing_constraints.get("seconds")
            if expected_seconds:
                elapsed = detection_time - stage_start_time
                if elapsed > expected_seconds:
                    result["timing_passed"] = False
                    result["violation"] = True
                    result["violation_reason"] = "late_behavior"
        
        return result

