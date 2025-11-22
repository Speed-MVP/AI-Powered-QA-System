"""
Phase 5: Rubric Validator Service
Validates RubricTemplate structure per Phase 5 spec.
"""

from typing import Tuple, List, Dict, Any
from app.models.rubric_template import RubricTemplate, RubricCategory, RubricMapping
from app.models.flow_version import FlowVersion
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class RubricValidator:
    """Validates RubricTemplate per Phase 5 spec"""
    
    @staticmethod
    def validate_weight_sum(categories: List[RubricCategory]) -> Tuple[bool, str]:
        """
        Validate that category weights sum to 100.
        Returns (is_valid, error_message)
        """
        total_weight = sum(float(c.weight) for c in categories)
        
        if abs(total_weight - 100.0) > 0.01:  # Allow small floating point differences
            return False, f"Category weights must sum to 100. Current sum: {total_weight}"
        
        return True, ""
    
    @staticmethod
    def validate_level_definitions(level_definitions: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate level definitions cover 0-100 with no gaps/overlaps.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        if not level_definitions:
            return True, []  # Empty is valid
        
        # Sort by min_score
        sorted_levels = sorted(level_definitions, key=lambda x: x.get("min_score", 0))
        
        # Check coverage from 0-100
        expected_start = 0
        
        for i, level in enumerate(sorted_levels):
            min_score = level.get("min_score", 0)
            max_score = level.get("max_score", 100)
            
            # Check for gaps
            if min_score > expected_start:
                errors.append(f"Gap in level definitions: {expected_start}-{min_score} not covered")
            
            # Check for overlaps
            if i > 0:
                prev_max = sorted_levels[i-1].get("max_score", 0)
                if min_score < prev_max:
                    errors.append(f"Overlap in level definitions: {min_score} overlaps with previous level ending at {prev_max}")
            
            # Validate min <= max
            if min_score > max_score:
                errors.append(f"Level '{level.get('name', 'unknown')}' has min_score ({min_score}) > max_score ({max_score})")
            
            expected_start = max_score + 1
        
        # Check if we cover to 100
        last_max = sorted_levels[-1].get("max_score", 0) if sorted_levels else 0
        if last_max < 100:
            errors.append(f"Level definitions do not cover to 100. Last level ends at {last_max}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_mapped_targets_exist(
        rubric_template: RubricTemplate,
        flow_version: FlowVersion
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all mapped targets (stages/steps) exist in FlowVersion.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Collect valid IDs
        valid_stage_ids = {s.id for s in flow_version.stages}
        valid_step_ids = set()
        for stage in flow_version.stages:
            for step in stage.steps:
                valid_step_ids.add(step.id)
        
        # Check all mappings
        for category in rubric_template.categories:
            for mapping in category.mappings:
                target_id = mapping.target_id
                
                if mapping.target_type == "stage":
                    if target_id not in valid_stage_ids:
                        errors.append(f"Category '{category.name}' maps to non-existent stage: {target_id}")
                elif mapping.target_type == "step":
                    if target_id not in valid_step_ids:
                        errors.append(f"Category '{category.name}' maps to non-existent step: {target_id}")
                else:
                    errors.append(f"Invalid target_type: {mapping.target_type}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_category_has_mappings(category: RubricCategory) -> Tuple[bool, str]:
        """Check if category has at least one mapping"""
        if not category.mappings or len(category.mappings) == 0:
            return False, f"Category '{category.name}' must have at least one mapped target"
        return True, ""
    
    @staticmethod
    def validate_rubric_template(
        rubric_template: RubricTemplate,
        flow_version: FlowVersion
    ) -> Tuple[bool, List[str]]:
        """
        Validate entire RubricTemplate structure.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate weight sum
        is_valid, error_msg = RubricValidator.validate_weight_sum(rubric_template.categories)
        if not is_valid:
            errors.append(error_msg)
        
        # Validate each category
        for category in rubric_template.categories:
            # Check mappings exist
            is_valid, error_msg = RubricValidator.validate_category_has_mappings(category)
            if not is_valid:
                errors.append(error_msg)
            
            # Validate level definitions
            level_defs = category.level_definitions
            if level_defs:
                is_valid, level_errors = RubricValidator.validate_level_definitions(level_defs)
                if not is_valid:
                    errors.extend([f"Category '{category.name}': {e}" for e in level_errors])
        
        # Validate mapped targets exist
        is_valid, target_errors = RubricValidator.validate_mapped_targets_exist(rubric_template, flow_version)
        if not is_valid:
            errors.extend(target_errors)
        
        return len(errors) == 0, errors

