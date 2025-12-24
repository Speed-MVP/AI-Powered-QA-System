"""
Blueprint Mapper Service - Phase 4
Maps Blueprint JSON to compiled artifacts (FlowVersion, FlowStage, FlowStep, ComplianceRule, RubricTemplate)
"""

import logging
import uuid
from typing import Dict, Any, List
from decimal import Decimal
from app.models.compiled_artifacts import (
    CompiledFlowVersion,
    CompiledFlowStage,
    CompiledFlowStep,
    CompiledComplianceRule,
    CompiledRubricTemplate,
    RuleType,
    Severity,
)
from app.models.qa_blueprint_behavior import BehaviorType, DetectionMode, CriticalAction

logger = logging.getLogger(__name__)


class BlueprintMapper:
    """Maps Blueprint to compiled artifacts"""
    
    def map_blueprint_to_artifacts(
        self,
        blueprint_snapshot: Dict[str, Any],
        blueprint_version_id: str,
        company_id: str
    ) -> Dict[str, Any]:
        """
        Map blueprint snapshot to compiled artifacts
        
        Returns:
            Dictionary with keys: flow_version, flow_stages, flow_steps, compliance_rules, rubric_template
        """
        # 1. Map to FlowVersion
        flow_version = self._map_to_flow_version(blueprint_snapshot, blueprint_version_id, company_id)
        
        # 2. Map stages to FlowStages
        flow_stages = []
        flow_steps = []
        compliance_rules = []
        
        for stage_data in blueprint_snapshot.get("stages", []):
            flow_stage = self._map_to_flow_stage(stage_data, flow_version["id"])
            flow_stages.append(flow_stage)
            
            # 3. Map behaviors to FlowSteps and ComplianceRules
            for behavior_data in stage_data.get("behaviors", []):
                flow_step = self._map_to_flow_step(behavior_data, flow_stage["id"], len(flow_steps))
                flow_steps.append(flow_step)
                
                # Create compliance rules for required/forbidden/critical behaviors
                behavior_rules = self._map_to_compliance_rules(
                    behavior_data,
                    flow_version["id"],
                    flow_step["id"],
                    flow_stage["id"]
                )
                compliance_rules.extend(behavior_rules)
        
        # 4. Map to RubricTemplate
        rubric_template = self._map_to_rubric_template(
            blueprint_snapshot,
            flow_version["id"],
            flow_stages,
            flow_steps
        )
        
        return {
            "flow_version": flow_version,
            "flow_stages": flow_stages,
            "flow_steps": flow_steps,
            "compliance_rules": compliance_rules,
            "rubric_template": rubric_template
        }
    
    def _map_to_flow_version(
        self,
        blueprint_snapshot: Dict[str, Any],
        blueprint_version_id: str,
        company_id: str
    ) -> Dict[str, Any]:
        """Map blueprint to FlowVersion"""
        blueprint_name = blueprint_snapshot.get("name", "Unnamed Blueprint")
        blueprint_id = blueprint_version_id.split("-")[0] if "-" in blueprint_version_id else blueprint_version_id[:8]
        
        # Create unique name: "{blueprint_name} (bp:{id} v{version})"
        # Extract version from blueprint_version_id if possible, otherwise use 1
        version = 1  # Will be set by compiler
        flow_version_name = f"{blueprint_name} (bp:{blueprint_id} v{version})"
        
        metadata = blueprint_snapshot.get("metadata", {})
        
        # Generate ID upfront so it can be used by child artifacts
        return {
            "id": str(uuid.uuid4()),  # Generate ID upfront
            "company_id": company_id,
            "blueprint_version_id": blueprint_version_id,
            "name": flow_version_name,
            "description": blueprint_snapshot.get("description"),
            "is_active": True,
            "version_number": 1,
            "language": metadata.get("language"),
            "metadata": {
                "retention": metadata.get("retention_days"),
                "pii_redaction_required": metadata.get("pii_redaction_required", True),
                "pii_preserve_raw_transcript": metadata.get("pii_preserve_raw_transcript", False),
                **metadata
            }
        }
    
    def _map_to_flow_stage(
        self,
        stage_data: Dict[str, Any],
        flow_version_id: str
    ) -> Dict[str, Any]:
        """Map stage to FlowStage"""
        metadata = stage_data.get("metadata", {})
        
        return {
            "id": str(uuid.uuid4()),  # Generate ID upfront
            "flow_version_id": flow_version_id,
            "name": stage_data.get("stage_name"),
            "ordering_index": stage_data.get("ordering_index"),
            "stage_weight": {"weight": float(stage_data.get("stage_weight", 0))} if stage_data.get("stage_weight") else None,
            "expected_duration_hint": metadata.get("expected_duration_hint"),
            "metadata": {
                "ui_label": metadata.get("ui_label"),
                "color": metadata.get("color"),
                "sample_window_seconds": metadata.get("sample_window_seconds"),
                **metadata
            }
        }
    
    def _map_to_flow_step(
        self,
        behavior_data: Dict[str, Any],
        stage_id: str,
        ordering_index: int
    ) -> Dict[str, Any]:
        """Map behavior to FlowStep"""
        detection_mode = behavior_data.get("detection_mode", "semantic")
        
        # ALWAYS preserve phrases regardless of detection_mode
        # Phrases provide valuable context for semantic matching too
        expected_phrases = None
        phrases = behavior_data.get("phrases", [])
        if phrases:
            # Convert to array of strings
            expected_phrases = [
                p if isinstance(p, str) else p.get("text", "")
                for p in phrases
            ]
            # Filter out empty strings
            expected_phrases = [p for p in expected_phrases if p]
            if not expected_phrases:
                expected_phrases = None
        
        metadata = behavior_data.get("metadata", {})
        
        return {
            "id": str(uuid.uuid4()),  # Generate ID upfront
            "stage_id": stage_id,
            "name": behavior_data.get("behavior_name"),
            "description": behavior_data.get("description"),
            "ordering_index": ordering_index,
            "expected_role": metadata.get("speaker", "agent"),
            "expected_phrases": expected_phrases,
            "detection_hint": detection_mode,
            "metadata": {
                "behavior_type": behavior_data.get("behavior_type"),
                "critical_action": behavior_data.get("critical_action"),
                "examples": metadata.get("examples"),
                "language_hint": metadata.get("language_hint"),
                **metadata
            }
        }
    
    def _map_to_compliance_rules(
        self,
        behavior_data: Dict[str, Any],
        flow_version_id: str,
        flow_step_id: str,
        stage_id: str
    ) -> List[Dict[str, Any]]:
        """Map behavior to ComplianceRules"""
        rules = []
        behavior_type = behavior_data.get("behavior_type", "required")
        detection_mode = behavior_data.get("detection_mode", "semantic")
        critical_action = behavior_data.get("critical_action")
        
        # Determine rule type
        if behavior_type == "forbidden":
            rule_type = RuleType.forbidden_phrase
            severity = Severity.major
        elif behavior_type == "critical":
            rule_type = RuleType.required_phrase if detection_mode != "semantic" else RuleType.required_step
            severity = Severity.critical
        elif behavior_type == "required":
            rule_type = RuleType.required_phrase if detection_mode != "semantic" else RuleType.required_step
            severity = Severity.major
        else:
            # Optional behaviors don't create compliance rules
            return []
        
        # ALWAYS get phrases regardless of detection_mode
        # Phrases are valuable for semantic matching context too
        phrases = None
        phrases_list = behavior_data.get("phrases", [])
        if phrases_list:
            phrases = [
                p if isinstance(p, str) else p.get("text", "")
                for p in phrases_list
            ]
            # Filter out empty strings
            phrases = [p for p in phrases if p]
            if not phrases:
                phrases = None
        
        # Determine match mode
        match_mode = None
        if detection_mode == "exact_phrase":
            match_mode = "exact"
        elif detection_mode == "semantic":
            match_mode = "semantic"
        elif detection_mode == "hybrid":
            match_mode = "hybrid"
        
        # Get timing constraints from metadata
        timing_constraints = None
        metadata = behavior_data.get("metadata", {})
        if "timing_requirement" in metadata:
            timing_constraints = metadata["timing_requirement"]
        
        rule = {
            "flow_version_id": flow_version_id,
            "flow_step_id": flow_step_id,
            "rule_type": rule_type.value,
            "target": flow_step_id,
            "phrases": phrases,
            "match_mode": match_mode,
            "severity": severity.value,
            "action_on_fail": critical_action if critical_action else None,
            "timing_constraints": timing_constraints,
            "active": True
        }
        
        rules.append(rule)
        
        return rules
    
    def _map_to_rubric_template(
        self,
        blueprint_snapshot: Dict[str, Any],
        flow_version_id: str,
        flow_stages: List[Dict[str, Any]],
        flow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Map blueprint to RubricTemplate"""
        # Each FlowStage becomes a rubric category
        categories = []
        mappings = []
        
        # Calculate total stage weight for normalization
        total_stage_weight = sum(
            float(s.get("stage_weight", {}).get("weight", 0)) if s.get("stage_weight") else 0
            for s in flow_stages
        )
        
        # If no weights specified, distribute evenly
        if total_stage_weight == 0:
            weight_per_stage = 100.0 / len(flow_stages) if flow_stages else 0
        else:
            # Normalize to 100
            weight_per_stage = 100.0 / total_stage_weight if total_stage_weight > 0 else 0
        
        # Create categories from stages
        stage_id_to_category = {}
        for stage in flow_stages:
            stage_weight = stage.get("stage_weight", {}).get("weight") if stage.get("stage_weight") else None
            if stage_weight:
                normalized_weight = (float(stage_weight) / total_stage_weight * 100) if total_stage_weight > 0 else weight_per_stage
            else:
                normalized_weight = weight_per_stage
            
            category_id = f"cat-{stage['name']}"
            category = {
                "id": category_id,
                "name": stage["name"],
                "weight": normalized_weight
            }
            categories.append(category)
            # Map stage to category for later use
            stage_id_to_category[stage.get("id") or stage["name"]] = category
        
        # Create mappings from behaviors to categories
        # Group flow_steps by stage
        steps_by_stage = {}
        for step in flow_steps:
            stage_id = step["stage_id"]
            if stage_id not in steps_by_stage:
                steps_by_stage[stage_id] = []
            steps_by_stage[stage_id].append(step)
        
        # Create mappings
        for stage in flow_stages:
            stage_id = stage.get("id") if "id" in stage else stage["name"]
            
            # Find category for this stage
            category = stage_id_to_category.get(stage_id)
            if not category:
                # Fallback: find by name
                category = next((c for c in categories if c["name"] == stage["name"]), None)
                if not category:
                    continue
            
            # Get steps for this stage
            stage_steps = steps_by_stage.get(stage_id, [])
            
            # Create mappings
            for step in stage_steps:
                # Contribution weight: distribute stage weight evenly across behaviors
                # In production, this would use actual behavior weights from blueprint
                contribution_weight = (category["weight"] / len(stage_steps)) if stage_steps else 0
                
                mapping = {
                    "category_id": category["id"],
                    "flow_step_id": f"step-{step['name']}",  # Will be replaced with actual ID during persistence
                    "contribution_weight": contribution_weight
                }
                mappings.append(mapping)
        
        return {
            "flow_version_id": flow_version_id,
            "name": f"Rubric for {blueprint_snapshot.get('name', 'Blueprint')}",
            "categories": categories,
            "mappings": mappings
        }

