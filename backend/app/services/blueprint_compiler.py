"""
Blueprint Compiler Service - Phase 4
Orchestrates the compilation of Blueprints to compiled artifacts
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.qa_blueprint_version import QABlueprintVersion
from app.models.compiled_artifacts import (
    CompiledFlowVersion,
    CompiledFlowStage,
    CompiledFlowStep,
    CompiledComplianceRule,
    CompiledRubricTemplate,
)
from app.services.blueprint_mapper import BlueprintMapper
from app.services.blueprint_validator import BlueprintValidator
from app.services.monitoring import monitoring_service
import uuid
import time

logger = logging.getLogger(__name__)


class CompilerError:
    """Represents a compiler error"""
    def __init__(self, code: str, message: str, field: Optional[str] = None):
        self.code = code
        self.message = message
        self.field = field
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "field": self.field
        }


class BlueprintCompiler:
    """Compiles Blueprints to internal artifacts"""
    
    def __init__(self):
        self.mapper = BlueprintMapper()
        self.validator = BlueprintValidator()
    
    def compile_blueprint_version(
        self,
        blueprint_version: QABlueprintVersion,
        db: Session,
        compile_options: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], List[CompilerError], List[str]]:
        """
        Compile a blueprint version to artifacts
        
        Returns:
            Tuple of (success, compiled_artifacts_dict, errors, warnings)
        """
        compile_options = compile_options or {}
        errors: List[CompilerError] = []
        warnings: List[str] = []
        
        start_time = time.time()
        
        try:
            # 1. Get blueprint snapshot
            snapshot = blueprint_version.snapshot
            
            # 2. Validate snapshot structure
            validation_errors = self._validate_snapshot_structure(snapshot)
            if validation_errors:
                errors.extend(validation_errors)
                return False, None, errors, warnings
            
            # 3. Map to artifacts
            try:
                artifacts = self.mapper.map_blueprint_to_artifacts(
                    blueprint_snapshot=snapshot,
                    blueprint_version_id=blueprint_version.id,
                    company_id=blueprint_version.blueprint.company_id
                )
            except Exception as e:
                logger.error(f"Mapping failed: {e}", exc_info=True)
                errors.append(CompilerError(
                    "MAPPING_FAILED",
                    f"Failed to map blueprint to artifacts: {str(e)}"
                ))
                return False, None, errors, warnings
            
            # 4. Validate generated artifacts
            artifact_errors = self._validate_artifacts(artifacts)
            if artifact_errors:
                errors.extend(artifact_errors)
                return False, None, errors, warnings
            
            # 5. Generate policy rules if requested (optional, LLM-assisted)
            if compile_options.get("generate_policy_rules", False):
                try:
                    policy_rules = self._generate_policy_rules(artifacts, compile_options)
                    artifacts["policy_rules"] = policy_rules
                except Exception as e:
                    logger.warning(f"Policy rule generation failed: {e}")
                    warnings.append(f"Policy rule generation failed: {str(e)}")
            
            duration = time.time() - start_time
            
            # Record metrics
            monitoring_service.record_compiler_metric(
                blueprint_id=blueprint_version.blueprint.id,
                success=True,
                duration_seconds=duration,
                errors=[],
                warnings=warnings
            )
            
            return True, artifacts, errors, warnings
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Compilation failed: {e}", exc_info=True)
            errors.append(CompilerError(
                "COMPILATION_FAILED",
                f"Compilation failed: {str(e)}"
            ))
            
            # Record metrics
            monitoring_service.record_compiler_metric(
                blueprint_id=blueprint_version.blueprint.id,
                success=False,
                duration_seconds=duration,
                errors=[str(e)],
                warnings=warnings
            )
            
            return False, None, errors, warnings
    
    def _validate_snapshot_structure(self, snapshot: Dict[str, Any]) -> List[CompilerError]:
        """Validate blueprint snapshot structure"""
        errors = []
        
        if not isinstance(snapshot, dict):
            errors.append(CompilerError("INVALID_SNAPSHOT", "Snapshot must be a JSON object"))
            return errors
        
        if "name" not in snapshot or not snapshot["name"]:
            errors.append(CompilerError("MISSING_NAME", "Blueprint name is required", "name"))
        
        if "stages" not in snapshot or not isinstance(snapshot["stages"], list):
            errors.append(CompilerError("NO_STAGES", "At least one stage must exist", "stages"))
        elif len(snapshot["stages"]) == 0:
            errors.append(CompilerError("NO_STAGES", "At least one stage must exist", "stages"))
        
        return errors
    
    def _validate_artifacts(self, artifacts: Dict[str, Any]) -> List[CompilerError]:
        """Validate generated artifacts"""
        errors = []
        
        # Validate flow_version
        if "flow_version" not in artifacts:
            errors.append(CompilerError("MISSING_FLOW_VERSION", "FlowVersion artifact is missing"))
        
        # Validate flow_stages
        if "flow_stages" not in artifacts or not artifacts["flow_stages"]:
            errors.append(CompilerError("MISSING_FLOW_STAGES", "FlowStage artifacts are missing"))
        
        # Validate flow_steps
        if "flow_steps" not in artifacts or not artifacts["flow_steps"]:
            errors.append(CompilerError("MISSING_FLOW_STEPS", "FlowStep artifacts are missing"))
        
        # Validate rubric_template
        if "rubric_template" not in artifacts:
            errors.append(CompilerError("MISSING_RUBRIC_TEMPLATE", "RubricTemplate artifact is missing"))
        else:
            rubric = artifacts["rubric_template"]
            if "categories" not in rubric or not rubric["categories"]:
                errors.append(CompilerError("MISSING_RUBRIC_CATEGORIES", "RubricTemplate must have categories"))
            if "mappings" not in rubric:
                errors.append(CompilerError("MISSING_RUBRIC_MAPPINGS", "RubricTemplate must have mappings"))
        
        return errors
    
    def _generate_policy_rules(
        self,
        artifacts: Dict[str, Any],
        compile_options: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate policy rules via LLM (optional)
        
        This is a placeholder - full implementation would use PolicyRuleBuilder service
        """
        # TODO: Implement LLM-assisted policy rule generation
        # For now, return None (rules are created from behaviors via mapper)
        return None
    
    def persist_artifacts(
        self,
        artifacts: Dict[str, Any],
        db: Session
    ) -> Dict[str, str]:
        """
        Persist compiled artifacts to database
        
        Returns:
            Dictionary mapping artifact type to ID
        """
        artifact_ids = {}
        
        try:
            # 1. Create CompiledFlowVersion
            flow_version_data = artifacts["flow_version"]
            flow_version = CompiledFlowVersion(**flow_version_data)
            db.add(flow_version)
            db.flush()
            artifact_ids["flow_version_id"] = flow_version.id
            
            # 2. Create CompiledFlowStages
            stage_ids = {}
            for stage_data in artifacts["flow_stages"]:
                stage_data["flow_version_id"] = flow_version.id
                stage = CompiledFlowStage(**stage_data)
                db.add(stage)
                db.flush()
                stage_ids[stage_data.get("id") or stage.id] = stage.id
            
            # 3. Create CompiledFlowSteps
            step_ids = {}
            for step_data in artifacts["flow_steps"]:
                # Map stage_id from old to new
                old_stage_id = step_data["stage_id"]
                new_stage_id = stage_ids.get(old_stage_id, old_stage_id)
                step_data["stage_id"] = new_stage_id
                
                step = CompiledFlowStep(**step_data)
                db.add(step)
                db.flush()
                step_ids[step_data.get("id") or step.id] = step.id
            
            # 4. Create CompiledComplianceRules
            for rule_data in artifacts.get("compliance_rules", []):
                rule_data["flow_version_id"] = flow_version.id
                # Map flow_step_id
                old_step_id = rule_data.get("flow_step_id")
                if old_step_id:
                    rule_data["flow_step_id"] = step_ids.get(old_step_id, old_step_id)
                
                rule = CompiledComplianceRule(**rule_data)
                db.add(rule)
            
            # 5. Create CompiledRubricTemplate
            rubric_data = artifacts["rubric_template"].copy()
            rubric_data["flow_version_id"] = flow_version.id
            
            # Update step IDs in mappings using step names
            # Map step names to IDs
            step_name_to_id = {}
            for step in db.query(CompiledFlowStep).filter(
                CompiledFlowStep.stage_id.in_([s.id for s in db.query(CompiledFlowStage).filter(
                    CompiledFlowStage.flow_version_id == flow_version.id
                ).all()])
            ).all():
                step_name_to_id[step.name] = step.id
            
            # Update mappings with actual step IDs
            updated_mappings = []
            for mapping in rubric_data.get("mappings", []):
                step_name = mapping.get("flow_step_id", "").replace("step-", "")
                actual_step_id = step_name_to_id.get(step_name)
                if actual_step_id:
                    mapping["flow_step_id"] = actual_step_id
                    updated_mappings.append(mapping)
            
            rubric_data["mappings"] = updated_mappings
            
            rubric = CompiledRubricTemplate(**rubric_data)
            db.add(rubric)
            db.flush()
            artifact_ids["rubric_template_id"] = rubric.id
            
            db.commit()
            
            return artifact_ids
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist artifacts: {e}", exc_info=True)
            raise

