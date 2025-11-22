"""
Phase 1: FlowVersion Validator Service
Validates FlowVersion structure according to Phase 1 requirements.
"""

from typing import List, Dict, Any, Tuple
from app.models.flow_version import FlowVersion
from app.models.flow_stage import FlowStage
from app.models.flow_step import FlowStep
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class FlowVersionValidator:
    """Validates FlowVersion structure per Phase 1 spec"""
    
    @staticmethod
    def validate_flow_version(flow_version: FlowVersion, db: Session) -> Tuple[bool, List[str]]:
        """
        Validate entire FlowVersion structure.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Flow-level validations
        if not flow_version.stages or len(flow_version.stages) == 0:
            errors.append("At least one stage must exist")
        
        # Stage validations
        stage_names = []
        stage_orders = []
        
        for stage in flow_version.stages:
            # Stage name validation
            if not stage.name or not stage.name.strip():
                errors.append(f"Stage '{stage.id}' has empty name")
            
            if stage.name in stage_names:
                errors.append(f"Duplicate stage name: '{stage.name}'")
            stage_names.append(stage.name)
            
            # Stage order validation
            if stage.order in stage_orders:
                errors.append(f"Duplicate stage order: {stage.order}")
            stage_orders.append(stage.order)
            
            # Each stage must have at least one step
            if not stage.steps or len(stage.steps) == 0:
                errors.append(f"Stage '{stage.name}' must have at least one step")
            
            # Step validations
            step_names = []
            step_orders = []
            
            for step in stage.steps:
                # Step name validation
                if not step.name or not step.name.strip():
                    errors.append(f"Step '{step.id}' in stage '{stage.name}' has empty name")
                
                # Step description validation
                if not step.description or not step.description.strip():
                    errors.append(f"Step '{step.name}' in stage '{stage.name}' has empty description")
                
                # Step name unique within stage
                if step.name in step_names:
                    errors.append(f"Duplicate step name '{step.name}' in stage '{stage.name}'")
                step_names.append(step.name)
                
                # Step order validation
                if step.order in step_orders:
                    errors.append(f"Duplicate step order {step.order} in stage '{stage.name}'")
                step_orders.append(step.order)
                
                # Timing requirement validation
                if step.timing_requirement:
                    timing = step.timing_requirement
                    if isinstance(timing, dict):
                        if timing.get("enabled") and (not timing.get("seconds") or timing.get("seconds") <= 0):
                            errors.append(
                                f"Step '{step.name}' in stage '{stage.name}' has timing enabled "
                                f"but invalid seconds value"
                            )
        
        # Validate ordering is sequential (no gaps)
        if stage_orders:
            sorted_orders = sorted(stage_orders)
            expected_orders = list(range(1, len(sorted_orders) + 1))
            if sorted_orders != expected_orders:
                errors.append(f"Stage orders must be sequential starting from 1. Found: {sorted_orders}")
        
        # Validate step orders are sequential within each stage
        for stage in flow_version.stages:
            if stage.steps:
                step_orders = sorted([s.order for s in stage.steps])
                expected_orders = list(range(1, len(step_orders) + 1))
                if step_orders != expected_orders:
                    errors.append(
                        f"Step orders in stage '{stage.name}' must be sequential starting from 1. "
                        f"Found: {step_orders}"
                    )
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_stage_name_unique(stage_name: str, flow_version_id: str, exclude_stage_id: str = None, db: Session = None) -> bool:
        """Check if stage name is unique within FlowVersion"""
        if not db:
            return True
        
        query = db.query(FlowStage).filter(
            FlowStage.flow_version_id == flow_version_id,
            FlowStage.name == stage_name
        )
        
        if exclude_stage_id:
            query = query.filter(FlowStage.id != exclude_stage_id)
        
        existing = query.first()
        return existing is None
    
    @staticmethod
    def validate_step_name_unique(step_name: str, stage_id: str, exclude_step_id: str = None, db: Session = None) -> bool:
        """Check if step name is unique within Stage"""
        if not db:
            return True
        
        query = db.query(FlowStep).filter(
            FlowStep.stage_id == stage_id,
            FlowStep.name == step_name
        )
        
        if exclude_step_id:
            query = query.filter(FlowStep.id != exclude_step_id)
        
        existing = query.first()
        return existing is None
    
    @staticmethod
    def validate_timing_requirement(timing_requirement: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate timing requirement structure.
        Returns (is_valid, error_message)
        """
        if not timing_requirement:
            return True, ""
        
        if not isinstance(timing_requirement, dict):
            return False, "Timing requirement must be a dictionary"
        
        enabled = timing_requirement.get("enabled", False)
        seconds = timing_requirement.get("seconds")
        
        if enabled and (seconds is None or seconds <= 0):
            return False, "When timing requirement is enabled, seconds must be a positive number"
        
        return True, ""

