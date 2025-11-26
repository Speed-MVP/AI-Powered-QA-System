"""
Monitoring & Metrics Service - Phase 10
Tracks metrics for compiler, detection, LLM, and scoring operations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import SessionLocal
from app.models.qa_blueprint_compiler_map import QABlueprintCompilerMap
from app.models.sandbox import SandboxRun, SandboxRunStatus
from app.models.evaluation import Evaluation, EvaluationStatus

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for tracking and reporting metrics"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds
    
    def record_compiler_metric(
        self,
        blueprint_id: str,
        success: bool,
        duration_seconds: float,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ):
        """Record compiler operation metric"""
        metric = {
            "type": "compiler",
            "blueprint_id": blueprint_id,
            "success": success,
            "duration_seconds": duration_seconds,
            "errors": errors or [],
            "warnings": warnings or [],
            "timestamp": datetime.utcnow()
        }
        logger.info(f"Compiler metric: {metric}")
        # In production, would store in metrics database or send to monitoring service
    
    def record_detection_metric(
        self,
        blueprint_id: str,
        behaviors_count: int,
        detected_count: int,
        avg_confidence: float,
        duration_seconds: float
    ):
        """Record detection engine metric"""
        metric = {
            "type": "detection",
            "blueprint_id": blueprint_id,
            "behaviors_count": behaviors_count,
            "detected_count": detected_count,
            "detection_rate": detected_count / behaviors_count if behaviors_count > 0 else 0,
            "avg_confidence": avg_confidence,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.utcnow()
        }
        logger.info(f"Detection metric: {metric}")
    
    def record_llm_metric(
        self,
        blueprint_id: str,
        stage_id: str,
        success: bool,
        tokens_used: int,
        cost_estimate: float,
        duration_seconds: float,
        error: Optional[str] = None
    ):
        """Record LLM evaluation metric"""
        metric = {
            "type": "llm",
            "blueprint_id": blueprint_id,
            "stage_id": stage_id,
            "success": success,
            "tokens_used": tokens_used,
            "cost_estimate": cost_estimate,
            "duration_seconds": duration_seconds,
            "error": error,
            "timestamp": datetime.utcnow()
        }
        logger.info(f"LLM metric: {metric}")
    
    def record_scoring_metric(
        self,
        blueprint_id: str,
        overall_score: float,
        passed: bool,
        stages_count: int,
        violations_count: int,
        duration_seconds: float
    ):
        """Record scoring engine metric"""
        metric = {
            "type": "scoring",
            "blueprint_id": blueprint_id,
            "overall_score": overall_score,
            "passed": passed,
            "stages_count": stages_count,
            "violations_count": violations_count,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.utcnow()
        }
        logger.info(f"Scoring metric: {metric}")
    
    def get_compiler_stats(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get compiler statistics"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count successful compilations
            successful = db.query(QABlueprintCompilerMap).filter(
                QABlueprintCompilerMap.created_at >= cutoff_date,
                QABlueprintCompilerMap.flow_version_id.isnot(None)
            ).count()
            
            # Count total compilation attempts (from audit logs or compiler maps)
            total = db.query(QABlueprintCompilerMap).filter(
                QABlueprintCompilerMap.created_at >= cutoff_date
            ).count()
            
            success_rate = (successful / total * 100) if total > 0 else 0
            
            return {
                "total_compilations": total,
                "successful_compilations": successful,
                "failed_compilations": total - successful,
                "success_rate": round(success_rate, 2),
                "period_days": days
            }
        finally:
            db.close()
    
    def get_detection_stats(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get detection engine statistics"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get evaluations with detection results
            evaluations = db.query(Evaluation).filter(
                Evaluation.created_at >= cutoff_date,
                Evaluation.deterministic_results.isnot(None)
            ).all()
            
            total_behaviors = 0
            total_detected = 0
            total_confidence = 0.0
            count = 0
            
            for eval in evaluations:
                if eval.deterministic_results and "behaviors" in eval.deterministic_results:
                    behaviors = eval.deterministic_results["behaviors"]
                    total_behaviors += len(behaviors)
                    detected = sum(1 for b in behaviors if b.get("detected", False))
                    total_detected += detected
                    confidences = [b.get("confidence", 0) for b in behaviors if b.get("detected")]
                    if confidences:
                        total_confidence += sum(confidences) / len(confidences)
                    count += 1
            
            avg_confidence = total_confidence / count if count > 0 else 0
            detection_rate = (total_detected / total_behaviors * 100) if total_behaviors > 0 else 0
            
            return {
                "total_evaluations": count,
                "total_behaviors_checked": total_behaviors,
                "total_behaviors_detected": total_detected,
                "detection_rate": round(detection_rate, 2),
                "avg_confidence": round(avg_confidence, 3),
                "period_days": days
            }
        finally:
            db.close()
    
    def get_llm_stats(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get LLM evaluation statistics"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            evaluations = db.query(Evaluation).filter(
                Evaluation.created_at >= cutoff_date,
                Evaluation.llm_stage_evaluations.isnot(None)
            ).all()
            
            total_tokens = 0
            total_cost = 0.0
            successful = 0
            failed = 0
            
            for eval in evaluations:
                if eval.llm_stage_evaluations:
                    # Count stages evaluated
                    stages = eval.llm_stage_evaluations
                    if isinstance(stages, dict):
                        successful += len(stages)
                    # Estimate tokens (placeholder - would track actual tokens)
                    total_tokens += 1000  # Placeholder
                    total_cost += 0.01  # Placeholder
            
            return {
                "total_stage_evaluations": successful + failed,
                "successful_evaluations": successful,
                "failed_evaluations": failed,
                "success_rate": round((successful / (successful + failed) * 100) if (successful + failed) > 0 else 0, 2),
                "total_tokens_estimated": total_tokens,
                "total_cost_estimated": round(total_cost, 4),
                "period_days": days
            }
        finally:
            db.close()
    
    def get_scoring_stats(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get scoring engine statistics"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            evaluations = db.query(Evaluation).filter(
                Evaluation.created_at >= cutoff_date,
                Evaluation.final_evaluation.isnot(None)
            ).all()
            
            total_score = 0.0
            passed_count = 0
            total_violations = 0
            count = len(evaluations)
            
            for eval in evaluations:
                if eval.final_evaluation:
                    total_score += eval.overall_score
                    if eval.overall_passed:
                        passed_count += 1
                    violations = eval.final_evaluation.get("policy_violations", [])
                    total_violations += len(violations)
            
            avg_score = total_score / count if count > 0 else 0
            pass_rate = (passed_count / count * 100) if count > 0 else 0
            
            return {
                "total_evaluations": count,
                "avg_score": round(avg_score, 2),
                "passed_count": passed_count,
                "failed_count": count - passed_count,
                "pass_rate": round(pass_rate, 2),
                "total_violations": total_violations,
                "avg_violations_per_evaluation": round(total_violations / count, 2) if count > 0 else 0,
                "period_days": days
            }
        finally:
            db.close()
    
    def get_sandbox_stats(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get sandbox statistics"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            runs = db.query(SandboxRun).filter(
                SandboxRun.created_at >= cutoff_date
            ).all()
            
            total = len(runs)
            succeeded = sum(1 for r in runs if r.status == SandboxRunStatus.succeeded)
            failed = sum(1 for r in runs if r.status == SandboxRunStatus.failed)
            running = sum(1 for r in runs if r.status == SandboxRunStatus.running)
            
            return {
                "total_runs": total,
                "succeeded": succeeded,
                "failed": failed,
                "running": running,
                "success_rate": round((succeeded / total * 100) if total > 0 else 0, 2),
                "period_days": days
            }
        finally:
            db.close()
    
    def get_all_metrics(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get all metrics summary"""
        return {
            "compiler": self.get_compiler_stats(company_id, days),
            "detection": self.get_detection_stats(company_id, days),
            "llm": self.get_llm_stats(company_id, days),
            "scoring": self.get_scoring_stats(company_id, days),
            "sandbox": self.get_sandbox_stats(company_id, days),
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }


# Singleton instance
monitoring_service = MonitoringService()

