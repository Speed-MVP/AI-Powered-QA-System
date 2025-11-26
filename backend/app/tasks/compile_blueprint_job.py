"""
Compile Blueprint Job - Phase 4
Cloud Tasks handler for blueprint compilation
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.qa_blueprint import QABlueprint, BlueprintStatus
from app.models.qa_blueprint_version import QABlueprintVersion
from app.models.qa_blueprint_compiler_map import QABlueprintCompilerMap
from app.services.blueprint_compiler import BlueprintCompiler
import uuid

logger = logging.getLogger(__name__)


async def compile_blueprint_job_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle blueprint compilation job from Cloud Tasks
    
    Args:
        payload: {
            "blueprint_id": str,
            "blueprint_version_id": str,
            "compile_options": dict,
            "user_id": str
        }
    
    Returns:
        Job result dictionary
    """
    db = SessionLocal()
    try:
        blueprint_id = payload.get("blueprint_id")
        blueprint_version_id = payload.get("blueprint_version_id")
        compile_options = payload.get("compile_options", {})
        user_id = payload.get("user_id")
        
        logger.info(f"Starting compilation job for blueprint {blueprint_id}, version {blueprint_version_id}")
        
        # Get blueprint version
        blueprint_version = db.query(QABlueprintVersion).filter(
            QABlueprintVersion.id == blueprint_version_id
        ).first()
        
        if not blueprint_version:
            logger.error(f"Blueprint version {blueprint_version_id} not found")
            return {
                "status": "failed",
                "error": "Blueprint version not found"
            }
        
        # Check if already compiled
        existing_map = db.query(QABlueprintCompilerMap).filter(
            QABlueprintCompilerMap.blueprint_version_id == blueprint_version_id
        ).first()
        
        if existing_map and existing_map.flow_version_id:
            logger.info(f"Blueprint version {blueprint_version_id} already compiled")
            return {
                "status": "succeeded",
                "compiled_flow_version_id": existing_map.flow_version_id,
                "message": "Already compiled"
            }
        
        # Compile blueprint
        compiler = BlueprintCompiler()
        success, artifacts, errors, warnings = compiler.compile_blueprint_version(
            blueprint_version=blueprint_version,
            db=db,
            compile_options=compile_options
        )
        
        if not success:
            logger.error(f"Compilation failed: {errors}")
            return {
                "status": "failed",
                "errors": [e.to_dict() for e in errors],
                "warnings": warnings
            }
        
        # Persist artifacts
        try:
            artifact_ids = compiler.persist_artifacts(artifacts, db)
        except Exception as e:
            logger.error(f"Failed to persist artifacts: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": f"Failed to persist artifacts: {str(e)}"
            }
        
        # Create compiler map
        compiler_map = QABlueprintCompilerMap(
            blueprint_version_id=blueprint_version_id,
            flow_version_id=artifact_ids.get("flow_version_id"),
            rubric_template_id=artifact_ids.get("rubric_template_id")
        )
        db.add(compiler_map)
        
        # Update blueprint version with compiled_flow_version_id
        blueprint_version.compiled_flow_version_id = artifact_ids.get("flow_version_id")
        
        # Update blueprint status to published
        blueprint = blueprint_version.blueprint
        blueprint.status = BlueprintStatus.published
        blueprint.compiled_flow_version_id = artifact_ids.get("flow_version_id")
        
        db.commit()
        
        logger.info(f"Compilation succeeded for blueprint {blueprint_id}")
        
        return {
            "status": "succeeded",
            "compiled_flow_version_id": artifact_ids.get("flow_version_id"),
            "warnings": warnings
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Compilation job failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()

