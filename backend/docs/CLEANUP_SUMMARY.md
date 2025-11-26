# Legacy Code Cleanup Summary

## Complete Removal of Legacy Code

All legacy FlowVersion/FlowStage/FlowStep system code has been completely removed from the codebase. The system now exclusively uses the Blueprint-based architecture.

## Files Removed ✅

### Services (9 files)
1. ✅ `backend/app/services/rubric_scorer.py` - Replaced by `scoring_engine.py`
2. ✅ `backend/app/services/rubric_validator.py` - Replaced by `blueprint_validator.py`
3. ✅ `backend/app/services/compliance_rule_validator.py` - Replaced by `blueprint_validator.py`
4. ✅ `backend/app/services/flow_version_validator.py` - Replaced by `blueprint_validator.py`
5. ✅ `backend/app/services/policy_rules_versioning.py` - Removed (PolicyTemplate system)
6. ✅ `backend/app/services/deterministic_llm_evaluator.py` - Removed (PolicyTemplate system)
7. ✅ `backend/app/services/gemini.py.evaluate()` - Removed (legacy method)
8. ✅ `backend/app/services/gemini.py._retrieve_similar_human_reviews()` - Removed (legacy method)
9. ✅ `backend/app/services/rag.py.retrieve_relevant_policies()` - Removed (evaluation_criteria system)

### Tasks (2 files)
1. ✅ `backend/app/tasks/process_recording_phase7.py` - Replaced by `process_recording_blueprint.py`
2. ✅ `backend/app/tasks/generate_policy_rules_job.py` - Removed (PolicyTemplate system)

### Models (8 files + 1 class)
1. ✅ `backend/app/models/compliance_rule.py` - Legacy model (table dropped by migration)
2. ✅ `backend/app/models/rubric_template.py` - Legacy model (table dropped by migration)
3. ✅ `backend/app/models/policy_rules_version.py` - Removed (PolicyTemplate system)
4. ✅ `backend/app/models/policy_rules_draft.py` - Removed (PolicyTemplate system)
5. ✅ `backend/app/models/rule_audit_log.py` - Removed (PolicyTemplate system)
6. ✅ `backend/app/models/rule_version.py` - Removed (PolicyTemplate system)
7. ✅ `backend/app/models/rule_draft.py` - Removed (PolicyTemplate system)
8. ✅ `backend/app/models/_legacy_deprecated.py` - Documentation file
9. ✅ `EvaluationVersion` class removed from `backend/app/models/audit.py` - Replaced by AuditLog storage

### Schemas (4 files + 1 export)
1. ✅ `backend/app/schemas/flow_version.py` - Replaced by `blueprint.py`
2. ✅ `backend/app/schemas/compliance_rule.py` - No longer used
3. ✅ `backend/app/schemas/rubric_template.py` - No longer used
4. ✅ `backend/app/schemas/rubric_level.py` - No longer used
5. ✅ `CategoryScoreResponse` removed from `backend/app/schemas/__init__.py` exports

### Scripts (1 file)
1. ✅ `check_flow_steps.py` - Legacy utility script

### Tests (1 file)
1. ✅ `backend/app/tests/test_policy_rules_versioning.py` - Removed (PolicyTemplate system)

### Code Updates
1. ✅ `backend/app/services/audit.py` - Updated to use AuditLog instead of EvaluationVersion table
2. ✅ `backend/app/models/audit.py` - Removed EvaluationVersion model class
3. ✅ `backend/app/models/company.py` - Legacy FlowVersion relationship commented out
4. ✅ `backend/app/schemas/evaluation.py` - Legacy fields removed, only Blueprint structure remains

**Total: 20+ files/code sections removed**

## Database Tables (Removed by Migration)

The following legacy tables have been dropped by migration `remove_all_legacy_tables.py`:

1. `flow_versions` (Legacy Phase 1)
2. `flow_stages` (Legacy Phase 1)
3. `flow_steps` (Legacy Phase 1)
4. `compliance_rules` (Legacy Phase 2)
5. `rubric_templates` (Legacy Phase 5)
6. `rubric_categories` (Legacy Phase 5)
7. `rubric_mappings` (Legacy Phase 5)
8. `policy_templates` (Removed by earlier migration)
9. `evaluation_criteria` (Removed by earlier migration)
10. `policy_rules_versions` (Removed by earlier migration)
11. `policy_rules_drafts` (Removed by earlier migration)
12. `rule_audit_logs` (Removed by earlier migration)
13. `rule_versions` (Removed by earlier migration)
14. `rule_drafts` (Removed by earlier migration)

**Note**: All legacy migrations are preserved for reference only. Do not roll back in production.

## Current System Architecture

### Active Models (Blueprint System)
- ✅ `QABlueprint`, `QABlueprintStage`, `QABlueprintBehavior` - Primary Blueprint structure
- ✅ `CompiledFlowVersion`, `CompiledFlowStage`, `CompiledFlowStep` - Compiled artifacts
- ✅ `CompiledComplianceRule`, `CompiledRubricTemplate` - Compiled rules/scoring
- ✅ `Evaluation` - Uses `final_evaluation` JSONB with Blueprint structure

### Active Services
- ✅ `EvaluationPipeline` - Main orchestrator
- ✅ `DetectionEngine` - Uses CompiledFlowVersion
- ✅ `LLMStageEvaluator` - Uses CompiledFlowVersion protocols
- ✅ `ScoringEngine` - Uses CompiledRubricTemplate
- ✅ `BlueprintCompiler` - Compiles Blueprints to artifacts
- ✅ `BlueprintValidator` - Validates Blueprint structure

### Active Tasks
- ✅ `process_recording_blueprint.py` - Main recording processing
- ✅ `sandbox_worker.py` - Sandbox evaluation
- ✅ `compile_blueprint_job.py` - Blueprint compilation

## Verification

✅ No imports of legacy models (`FlowVersion`, `FlowStage`, `FlowStep`, `CategoryScore`, `RuleEngineResults`, `ComplianceRule`, `RubricTemplate`)
✅ No references to legacy services (`RubricScorer`, `RubricValidator`, `ComplianceRuleValidator`, `FlowVersionValidator`)
✅ All evaluation code uses Blueprint structure (`stage_scores`, `policy_violations` in JSONB)
✅ All routes and APIs return Blueprint-based data
✅ Sandbox and Test page use Blueprint evaluation system


## Documentation

- ✅ `backend/docs/LEGACY_MIGRATIONS_REFERENCE.md` - Reference documentation for database migrations (preserved for reference only)
- ✅ `backend/docs/CLEANUP_SUMMARY.md` - This file

All legacy code has been successfully removed! The system now exclusively uses the Blueprint-based architecture with no backward compatibility.
