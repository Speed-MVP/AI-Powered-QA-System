"""
Blueprint Validator Service - Phase 2
Publish-time validations for Blueprints
"""

import logging
from typing import List, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.qa_blueprint import QABlueprint
from app.models.qa_blueprint_stage import QABlueprintStage
from app.models.qa_blueprint_behavior import QABlueprintBehavior

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error"""
    def __init__(self, field: str, message: str, code: str = None):
        self.field = field
        self.message = message
        self.code = code or "VALIDATION_ERROR"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "code": self.code
        }


class BlueprintValidator:
    """Validates blueprints for publishing"""
    
    def validate_for_publish(
        self,
        blueprint: QABlueprint,
        db: Session,
        force_normalize_weights: bool = False
    ) -> Tuple[bool, List[ValidationError], List[str]]:
        """
        Validate blueprint for publishing
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors: List[ValidationError] = []
        warnings: List[str] = []
        
        # 1. At least one stage exists
        if not blueprint.stages or len(blueprint.stages) == 0:
            errors.append(ValidationError(
                "stages",
                "At least one stage must exist",
                "NO_STAGES"
            ))
            return False, errors, warnings
        
        # 2. Each stage has at least one behavior
        for stage in blueprint.stages:
            if not stage.behaviors or len(stage.behaviors) == 0:
                errors.append(ValidationError(
                    f"stages[{stage.stage_name}].behaviors",
                    f"Stage '{stage.stage_name}' must have at least one behavior",
                    f"NO_BEHAVIORS_IN_STAGE:{stage.stage_name}"
                ))
        
        # 3. Unique stage names within blueprint
        stage_names = [s.stage_name for s in blueprint.stages]
        if len(stage_names) != len(set(stage_names)):
            duplicates = [name for name in stage_names if stage_names.count(name) > 1]
            errors.append(ValidationError(
                "stages",
                f"Duplicate stage names: {', '.join(set(duplicates))}",
                f"DUPLICATE_STAGE_NAME:{duplicates[0]}"
            ))
        
        # 4. Unique behavior names within stage
        for stage in blueprint.stages:
            behavior_names = [b.behavior_name for b in stage.behaviors]
            if len(behavior_names) != len(set(behavior_names)):
                duplicates = [name for name in behavior_names if behavior_names.count(name) > 1]
                errors.append(ValidationError(
                    f"stages[{stage.stage_name}].behaviors",
                    f"Duplicate behavior names in stage '{stage.stage_name}': {', '.join(set(duplicates))}",
                    f"DUPLICATE_BEHAVIOR_NAME:{duplicates[0]}"
                ))
        
        # 5. Each behavior weight >= 0
        for stage in blueprint.stages:
            for behavior in stage.behaviors:
                if behavior.weight < 0:
                    errors.append(ValidationError(
                        f"stages[{stage.stage_name}].behaviors[{behavior.behavior_name}].weight",
                        f"Behavior weight must be >= 0",
                        f"INVALID_BEHAVIOR_WEIGHT:{behavior.behavior_name}"
                    ))
        
        # 6. Stage weights sum to 100% (or auto-normalize)
        stage_weights_sum = sum(
            float(s.stage_weight) if s.stage_weight else 0
            for s in blueprint.stages
        )
        
        if stage_weights_sum > 0:
            # Check if sum is approximately 100 (tolerance 0.01)
            if abs(stage_weights_sum - 100.0) > 0.01:
                if force_normalize_weights:
                    warnings.append("Stage weights do not sum to 100% - will be auto-normalized")
                else:
                    errors.append(ValidationError(
                        "stages",
                        f"Stage weights sum to {stage_weights_sum}%, must equal 100% (or enable force_normalize_weights)",
                        "STAGE_WEIGHTS_MISMATCH"
                    ))
        
        # 7. For each stage, sum(behavior.weights) > 0 unless force_normalize_weights
        for stage in blueprint.stages:
            behavior_weights_sum = sum(float(b.weight) for b in stage.behaviors)
            if behavior_weights_sum == 0:
                if force_normalize_weights:
                    warnings.append(f"Stage '{stage.stage_name}' has all behavior weights = 0 - will be auto-normalized")
                else:
                    errors.append(ValidationError(
                        f"stages[{stage.stage_name}].behaviors",
                        f"Sum of behavior weights in stage '{stage.stage_name}' must be > 0 (or enable force_normalize_weights)",
                        f"BEHAVIOR_WEIGHTS_MISSING:{stage.stage_name}"
                    ))
        
        # 8. For behaviors with detection_mode != semantic, phrases must be present
        for stage in blueprint.stages:
            for behavior in stage.behaviors:
                if behavior.detection_mode != "semantic":
                    if not behavior.phrases or len(behavior.phrases) == 0:
                        errors.append(ValidationError(
                            f"stages[{stage.stage_name}].behaviors[{behavior.behavior_name}].phrases",
                            f"phrases required for detection_mode '{behavior.detection_mode}'",
                            f"MISSING_PHRASES:{behavior.behavior_name}"
                        ))
                    else:
                        # Validate phrase length limits
                        for phrase in behavior.phrases:
                            if isinstance(phrase, str) and len(phrase) > 200:
                                errors.append(ValidationError(
                                    f"stages[{stage.stage_name}].behaviors[{behavior.behavior_name}].phrases",
                                    f"Phrase length must be <= 200 characters",
                                    "PHRASE_TOO_LONG"
                                ))
        
        # 9. Any critical behavior must have critical_action defined
        for stage in blueprint.stages:
            for behavior in stage.behaviors:
                if behavior.behavior_type == "critical" and not behavior.critical_action:
                    errors.append(ValidationError(
                        f"stages[{stage.stage_name}].behaviors[{behavior.behavior_name}].critical_action",
                        f"critical_action is required for critical behaviors",
                        "MISSING_CRITICAL_ACTION"
                    ))
        
        # 10. Check for contradictory rules (forbidden phrase that matches required phrase)
        for stage in blueprint.stages:
            required_phrases = set()
            forbidden_phrases = set()
            
            for behavior in stage.behaviors:
                if behavior.phrases:
                    phrases = [p if isinstance(p, str) else p.get("text", "") for p in behavior.phrases]
                    if behavior.behavior_type in ["required", "critical"]:
                        required_phrases.update(phrases)
                    elif behavior.behavior_type == "forbidden":
                        forbidden_phrases.update(phrases)
            
            conflicting = required_phrases.intersection(forbidden_phrases)
            if conflicting:
                errors.append(ValidationError(
                    f"stages[{stage.stage_name}]",
                    f"Contradictory rules: phrases {list(conflicting)} are both required and forbidden",
                    f"CONTRADICTORY_RULES:{list(conflicting)[0]}"
                ))
        
        # 11. Check for duplicate phrases across behaviors (warning only)
        for stage in blueprint.stages:
            all_phrases = {}
            for behavior in stage.behaviors:
                if behavior.phrases:
                    phrases = [p if isinstance(p, str) else p.get("text", "") for p in behavior.phrases]
                    for phrase in phrases:
                        if phrase in all_phrases:
                            warnings.append(f"Phrase '{phrase}' appears in multiple behaviors in stage '{stage.stage_name}'")
                        else:
                            all_phrases[phrase] = behavior.behavior_name
        
        # 12. Language metadata validation (warning if unsupported)
        if blueprint.extra_metadata and "language" in blueprint.extra_metadata:
            language = blueprint.extra_metadata.get("language", "").lower()
            supported_languages = ["en-us", "en", "es", "fr", "de"]
            if language and language not in supported_languages:
                warnings.append(f"Language '{language}' may not be fully supported")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def normalize_weights(
        self,
        blueprint: QABlueprint,
        normalize_stage_weights: bool = True,
        normalize_behavior_weights: bool = True
    ) -> None:
        """
        Normalize weights in blueprint
        
        Args:
            blueprint: The blueprint to normalize
            normalize_stage_weights: If True, normalize stage weights to sum to 100
            normalize_behavior_weights: If True, normalize behavior weights within each stage
        """
        if normalize_stage_weights:
            # Normalize stage weights to sum to 100
            stages_with_weights = [s for s in blueprint.stages if s.stage_weight]
            if stages_with_weights:
                total_weight = sum(float(s.stage_weight) for s in stages_with_weights)
                if total_weight > 0:
                    for stage in stages_with_weights:
                        stage.stage_weight = Decimal(str((float(stage.stage_weight) / total_weight) * 100))
                else:
                    # Evenly distribute
                    weight_per_stage = Decimal("100") / len(blueprint.stages)
                    for stage in blueprint.stages:
                        stage.stage_weight = weight_per_stage
        
        if normalize_behavior_weights:
            # Normalize behavior weights within each stage
            for stage in blueprint.stages:
                if not stage.behaviors:
                    continue
                
                total_behavior_weight = sum(float(b.weight) for b in stage.behaviors)
                stage_weight = float(stage.stage_weight) if stage.stage_weight else 100.0 / len(blueprint.stages)
                
                if total_behavior_weight > 0:
                    # Scale existing weights to stage_weight
                    for behavior in stage.behaviors:
                        behavior.weight = Decimal(str((float(behavior.weight) / total_behavior_weight) * stage_weight))
                else:
                    # Evenly distribute stage_weight across behaviors
                    weight_per_behavior = Decimal(str(stage_weight / len(stage.behaviors)))
                    for behavior in stage.behaviors:
                        behavior.weight = weight_per_behavior

