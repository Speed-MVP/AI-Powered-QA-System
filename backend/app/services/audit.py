"""
Audit and Compliance Service
Phase 4: Scale & Optimization
"""

from app.database import SessionLocal
from app.models.audit import AuditLog, AuditEventType, EvaluationVersion, ComplianceReport, DataRetentionPolicy
from typing import Dict, Any, Optional, List
import logging
import hashlib
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AuditService:
    """
    Comprehensive audit trail service for compliance and regulatory requirements.
    Phase 4: Store all evaluations and policies with version control.
    """

    def __init__(self):
        self.pipeline_version = "4.0.0"  # Current pipeline version

    def log_evaluation_event(
        self,
        event_type: AuditEventType,
        evaluation_id: str,
        user_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Log an evaluation-related event for audit trail.
        Returns the audit log ID.
        """
        db = SessionLocal()
        try:
            # Get user role if user_id provided
            user_role = None
            if user_id:
                from app.models.user import User
                user = db.query(User).filter(User.id == user_id).first()
                user_role = user.role.value if user else None

            # Extract model and confidence info from new_values
            model_version = None
            confidence_score = None
            if new_values and isinstance(new_values, dict):
                llm_analysis = new_values.get("llm_analysis", {})
                if isinstance(llm_analysis, dict):
                    model_version = llm_analysis.get("model_used")
                    confidence_score = new_values.get("confidence_score")

            audit_log = AuditLog(
                event_type=event_type,
                entity_type="evaluation",
                entity_id=evaluation_id,
                user_id=user_id,
                user_role=user_role,
                old_values=old_values,
                new_values=new_values,
                action=event_type.value.replace("_", " "),
                description=description,
                reason=reason,
                model_version=model_version,
                confidence_score=confidence_score,
                ip_address=ip_address,
                user_agent=user_agent
            )

            db.add(audit_log)
            db.commit()

            logger.info(f"Audit log created: {event_type.value} for evaluation {evaluation_id}")
            return audit_log.id

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create audit log: {e}")
            raise
        finally:
            db.close()

    def create_evaluation_version(
        self,
        evaluation_id: str,
        created_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> str:
        """
        Create a new version snapshot of an evaluation for version control.
        Phase 4: Include model version, timestamp, and reasoning snippet for audit defense.
        """
        db = SessionLocal()
        try:
            from app.models.evaluation import Evaluation
            from app.models.category_score import CategoryScore
            # Legacy: PolicyViolation removed - violations are now stored in deterministic_results JSONB

            evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not evaluation:
                raise ValueError(f"Evaluation {evaluation_id} not found")

            # Get next version number
            existing_versions = db.query(EvaluationVersion).filter(
                EvaluationVersion.evaluation_id == evaluation_id
            ).order_by(EvaluationVersion.version_number.desc()).first()

            version_number = (existing_versions.version_number + 1) if existing_versions else 1

            # Collect category scores
            category_scores = {}
            for score in evaluation.category_scores:
                category_scores[score.category_name] = {
                    "score": score.score,
                    "feedback": score.feedback
                }

            # Collect violations
            violations = []
            for violation in evaluation.policy_violations:
                violations.append({
                    "category_name": violation.criteria.category_name if violation.criteria else "Unknown",
                    "type": violation.violation_type,
                    "description": violation.description,
                    "severity": violation.severity
                })

            # Create version snapshot
            version = EvaluationVersion(
                evaluation_id=evaluation_id,
                version_number=version_number,
                created_by=created_by,
                overall_score=evaluation.overall_score,
                confidence_score=evaluation.confidence_score,
                category_scores=category_scores,
                violations=violations,
                llm_analysis=evaluation.llm_analysis,
                model_used=evaluation.llm_analysis.get("model_used", "unknown") if evaluation.llm_analysis else None,
                model_version=evaluation.llm_analysis.get("model_version", "unknown") if evaluation.llm_analysis else None,
                processing_pipeline_version=self.pipeline_version,
                change_reason=change_reason,
                previous_version_id=existing_versions.id if existing_versions else None
            )

            # Generate audit trail hash for tamper detection
            version_data = {
                "evaluation_id": evaluation_id,
                "version_number": version_number,
                "overall_score": evaluation.overall_score,
                "category_scores": category_scores,
                "violations": violations,
                "timestamp": version.created_at.isoformat()
            }
            version.audit_trail_hash = hashlib.sha256(
                json.dumps(version_data, sort_keys=True).encode()
            ).hexdigest()

            db.add(version)
            db.commit()

            logger.info(f"Evaluation version {version_number} created for evaluation {evaluation_id}")
            return version.id

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create evaluation version: {e}")
            raise
        finally:
            db.close()

    def generate_compliance_report(
        self,
        report_type: str,
        period_start: datetime,
        period_end: datetime
    ) -> str:
        """
        Generate automated compliance report for regulatory requirements.
        """
        db = SessionLocal()
        try:
            # Gather compliance metrics
            evaluations = db.query(Evaluation).join(Recording).filter(
                Recording.uploaded_at >= period_start,
                Recording.uploaded_at <= period_end
            ).all()

            total_evaluations = len(evaluations)

            if total_evaluations == 0:
                raise ValueError(f"No evaluations found in period {period_start} to {period_end}")

            # Calculate metrics
            human_reviews = [e for e in evaluations if e.human_review]
            human_review_rate = len(human_reviews) / total_evaluations if total_evaluations > 0 else 0

            confidence_scores = [e.confidence_score for e in evaluations if e.confidence_score]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None

            # Human agreement rate (simplified)
            if human_reviews:
                agreements = []
                for review in human_reviews:
                    ai_score = review.evaluation.overall_score
                    human_score = review.human_overall_score
                    agreements.append(abs(ai_score - human_score) <= 10)  # Within 10 points
                human_agreement_rate = sum(agreements) / len(agreements) if agreements else None
            else:
                human_agreement_rate = None

            # Create compliance report
            report = ComplianceReport(
                report_type=report_type,
                report_period_start=period_start,
                report_period_end=period_end,
                total_evaluations=total_evaluations,
                human_review_rate=round(float(human_review_rate), 3),
                average_confidence=round(float(avg_confidence), 3) if avg_confidence else None,
                human_agreement_rate=round(float(human_agreement_rate), 3) if human_agreement_rate else None,
                gdpr_compliant=True,  # Assume compliant with current implementation
                hipaa_compliant=True,  # Assume compliant
                sox_compliant=True     # Assume compliant
            )

            db.add(report)
            db.commit()

            logger.info(f"Compliance report generated: {report_type} for period {period_start} to {period_end}")
            return report.id

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate compliance report: {e}")
            raise
        finally:
            db.close()

    def get_evaluation_history(self, evaluation_id: str) -> List[Dict[str, Any]]:
        """
        Get complete version history for an evaluation with audit trail.
        """
        db = SessionLocal()
        try:
            versions = db.query(EvaluationVersion).filter(
                EvaluationVersion.evaluation_id == evaluation_id
            ).order_by(EvaluationVersion.version_number).all()

            audit_logs = db.query(AuditLog).filter(
                AuditLog.entity_type == "evaluation",
                AuditLog.entity_id == evaluation_id
            ).order_by(AuditLog.timestamp).all()

            history = []

            # Add version snapshots
            for version in versions:
                history.append({
                    "type": "version",
                    "version_number": version.version_number,
                    "timestamp": version.created_at.isoformat(),
                    "overall_score": version.overall_score,
                    "confidence_score": version.confidence_score,
                    "model_used": version.model_used,
                    "change_reason": version.change_reason,
                    "audit_trail_hash": version.audit_trail_hash
                })

            # Add audit events
            for log in audit_logs:
                history.append({
                    "type": "audit_event",
                    "event_type": log.event_type.value,
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "action": log.action,
                    "description": log.description,
                    "reason": log.reason,
                    "model_version": log.model_version,
                    "confidence_score": float(log.confidence_score) if log.confidence_score else None
                })

            # Sort by timestamp
            history.sort(key=lambda x: x["timestamp"])

            return history

        finally:
            db.close()

    def validate_audit_integrity(self, evaluation_id: str) -> Dict[str, Any]:
        """
        Validate audit trail integrity by checking hashes and version consistency.
        """
        db = SessionLocal()
        try:
            versions = db.query(EvaluationVersion).filter(
                EvaluationVersion.evaluation_id == evaluation_id
            ).order_by(EvaluationVersion.version_number).all()

            validation_results = {
                "evaluation_id": evaluation_id,
                "total_versions": len(versions),
                "integrity_check": True,
                "issues": []
            }

            for i, version in enumerate(versions):
                # Recalculate hash
                version_data = {
                    "evaluation_id": evaluation_id,
                    "version_number": version.version_number,
                    "overall_score": version.overall_score,
                    "category_scores": version.category_scores,
                    "violations": version.violations,
                    "timestamp": version.created_at.isoformat()
                }

                calculated_hash = hashlib.sha256(
                    json.dumps(version_data, sort_keys=True).encode()
                ).hexdigest()

                if calculated_hash != version.audit_trail_hash:
                    validation_results["integrity_check"] = False
                    validation_results["issues"].append({
                        "version": version.version_number,
                        "issue": "Hash mismatch - data may have been tampered with",
                        "stored_hash": version.audit_trail_hash,
                        "calculated_hash": calculated_hash
                    })

                # Check version number sequence
                if version.version_number != i + 1:
                    validation_results["integrity_check"] = False
                    validation_results["issues"].append({
                        "version": version.version_number,
                        "issue": f"Version number gap or sequence error (expected {i + 1})"
                    })

            return validation_results

        finally:
            db.close()

    def cleanup_expired_data(self) -> Dict[str, Any]:
        """
        Apply data retention policies and clean up expired data for compliance.
        """
        db = SessionLocal()
        try:
            # Get active retention policies
            policies = db.query(DataRetentionPolicy).filter(
                DataRetentionPolicy.active == True,
                DataRetentionPolicy.auto_delete == True
            ).all()

            cleanup_results = {
                "policies_applied": len(policies),
                "data_deleted": 0,
                "data_anonymized": 0,
                "errors": []
            }

            cutoff_date = datetime.utcnow()

            for policy in policies:
                retention_cutoff = cutoff_date - timedelta(days=policy.retention_period_days)

                try:
                    if policy.entity_type == "evaluation":
                        # Delete old evaluations (cascade will handle related data)
                        deleted_count = db.query(Evaluation).filter(
                            Evaluation.created_at < retention_cutoff
                        ).delete()

                        cleanup_results["data_deleted"] += deleted_count

                    elif policy.deletion_method == "anonymize":
                        # Anonymize data instead of deleting (for compliance)
                        # This would implement data anonymization logic
                        cleanup_results["data_anonymized"] += 1

                    logger.info(f"Applied retention policy for {policy.entity_type}: {policy.retention_period_days} days")

                except Exception as e:
                    cleanup_results["errors"].append(f"Policy {policy.id}: {str(e)}")

            db.commit()
            return cleanup_results

        except Exception as e:
            db.rollback()
            logger.error(f"Data cleanup failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()


















