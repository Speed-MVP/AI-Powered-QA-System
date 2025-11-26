"""
Alerts Service - Phase 10
Monitors for anomalies and triggers alerts
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.evaluation import Evaluation
from app.models.qa_blueprint_compiler_map import QABlueprintCompilerMap
from app.models.sandbox import SandboxRun, SandboxRunStatus
from app.services.monitoring import monitoring_service

logger = logging.getLogger(__name__)


class Alert:
    """Represents an alert"""
    def __init__(
        self,
        severity: str,
        title: str,
        message: str,
        metric_type: str,
        threshold: Optional[float] = None,
        actual_value: Optional[float] = None
    ):
        self.severity = severity  # critical, warning, info
        self.title = title
        self.message = message
        self.metric_type = metric_type
        self.threshold = threshold
        self.actual_value = actual_value
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "metric_type": self.metric_type,
            "threshold": self.threshold,
            "actual_value": self.actual_value,
            "timestamp": self.timestamp.isoformat()
        }


class AlertsService:
    """Service for detecting and reporting alerts"""
    
    def __init__(self):
        # Alert thresholds
        self.thresholds = {
            "llm_error_rate": 0.10,  # 10% error rate
            "compiler_failure_rate": 0.05,  # 5% failure rate
            "cost_per_evaluation": 0.10,  # $0.10 per evaluation
            "detection_confidence_low": 0.5,  # Average confidence below 50%
            "scoring_pass_rate_low": 0.60,  # Pass rate below 60%
            "sandbox_failure_rate": 0.20  # 20% sandbox failure rate
        }
    
    def check_llm_error_rate(
        self,
        company_id: Optional[str] = None,
        days: int = 1
    ) -> List[Alert]:
        """Check LLM error rate"""
        alerts = []
        stats = monitoring_service.get_llm_stats(company_id, days)
        
        total = stats.get("total_stage_evaluations", 0)
        failed = stats.get("failed_evaluations", 0)
        
        if total > 0:
            error_rate = failed / total
            threshold = self.thresholds["llm_error_rate"]
            
            if error_rate > threshold:
                alerts.append(Alert(
                    severity="critical" if error_rate > threshold * 2 else "warning",
                    title="High LLM Error Rate",
                    message=f"LLM evaluation error rate is {error_rate * 100:.1f}% (threshold: {threshold * 100:.1f}%)",
                    metric_type="llm_error_rate",
                    threshold=threshold,
                    actual_value=error_rate
                ))
        
        return alerts
    
    def check_compiler_failures(
        self,
        company_id: Optional[str] = None,
        days: int = 1
    ) -> List[Alert]:
        """Check compiler failure rate"""
        alerts = []
        stats = monitoring_service.get_compiler_stats(company_id, days)
        
        total = stats.get("total_compilations", 0)
        failed = stats.get("failed_compilations", 0)
        
        if total > 0:
            failure_rate = failed / total
            threshold = self.thresholds["compiler_failure_rate"]
            
            if failure_rate > threshold:
                alerts.append(Alert(
                    severity="critical" if failure_rate > threshold * 2 else "warning",
                    title="High Compiler Failure Rate",
                    message=f"Blueprint compilation failure rate is {failure_rate * 100:.1f}% (threshold: {threshold * 100:.1f}%)",
                    metric_type="compiler_failure_rate",
                    threshold=threshold,
                    actual_value=failure_rate
                ))
        
        return alerts
    
    def check_cost_anomalies(
        self,
        company_id: Optional[str] = None,
        days: int = 1
    ) -> List[Alert]:
        """Check for cost anomalies"""
        alerts = []
        stats = monitoring_service.get_llm_stats(company_id, days)
        
        total_evaluations = stats.get("total_stage_evaluations", 0)
        total_cost = stats.get("total_cost_estimated", 0)
        
        if total_evaluations > 0:
            cost_per_eval = total_cost / total_evaluations
            threshold = self.thresholds["cost_per_evaluation"]
            
            if cost_per_eval > threshold:
                alerts.append(Alert(
                    severity="warning",
                    title="High Cost Per Evaluation",
                    message=f"Average cost per evaluation is ${cost_per_eval:.4f} (threshold: ${threshold:.2f})",
                    metric_type="cost_per_evaluation",
                    threshold=threshold,
                    actual_value=cost_per_eval
                ))
        
        return alerts
    
    def check_detection_confidence(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> List[Alert]:
        """Check detection confidence levels"""
        alerts = []
        stats = monitoring_service.get_detection_stats(company_id, days)
        
        avg_confidence = stats.get("avg_confidence", 0)
        threshold = self.thresholds["detection_confidence_low"]
        
        if avg_confidence < threshold:
            alerts.append(Alert(
                severity="warning",
                title="Low Detection Confidence",
                message=f"Average detection confidence is {avg_confidence * 100:.1f}% (threshold: {threshold * 100:.1f}%)",
                metric_type="detection_confidence_low",
                threshold=threshold,
                actual_value=avg_confidence
            ))
        
        return alerts
    
    def check_scoring_pass_rate(
        self,
        company_id: Optional[str] = None,
        days: int = 7
    ) -> List[Alert]:
        """Check scoring pass rate"""
        alerts = []
        stats = monitoring_service.get_scoring_stats(company_id, days)
        
        pass_rate = stats.get("pass_rate", 100) / 100  # Convert to decimal
        threshold = self.thresholds["scoring_pass_rate_low"]
        
        if pass_rate < threshold:
            alerts.append(Alert(
                severity="warning",
                title="Low Pass Rate",
                message=f"Evaluation pass rate is {pass_rate * 100:.1f}% (threshold: {threshold * 100:.1f}%)",
                metric_type="scoring_pass_rate_low",
                threshold=threshold,
                actual_value=pass_rate
            ))
        
        return alerts
    
    def check_sandbox_failures(
        self,
        company_id: Optional[str] = None,
        days: int = 1
    ) -> List[Alert]:
        """Check sandbox failure rate"""
        alerts = []
        stats = monitoring_service.get_sandbox_stats(company_id, days)
        
        total = stats.get("total_runs", 0)
        failed = stats.get("failed", 0)
        
        if total > 0:
            failure_rate = failed / total
            threshold = self.thresholds["sandbox_failure_rate"]
            
            if failure_rate > threshold:
                alerts.append(Alert(
                    severity="warning",
                    title="High Sandbox Failure Rate",
                    message=f"Sandbox evaluation failure rate is {failure_rate * 100:.1f}% (threshold: {threshold * 100:.1f}%)",
                    metric_type="sandbox_failure_rate",
                    threshold=threshold,
                    actual_value=failure_rate
                ))
        
        return alerts
    
    def check_all_alerts(
        self,
        company_id: Optional[str] = None,
        days: int = 1
    ) -> List[Alert]:
        """Check all alert conditions"""
        alerts = []
        
        alerts.extend(self.check_llm_error_rate(company_id, days))
        alerts.extend(self.check_compiler_failures(company_id, days))
        alerts.extend(self.check_cost_anomalies(company_id, days))
        alerts.extend(self.check_detection_confidence(company_id, days))
        alerts.extend(self.check_scoring_pass_rate(company_id, days))
        alerts.extend(self.check_sandbox_failures(company_id, days))
        
        # Sort by severity (critical first)
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: severity_order.get(a.severity, 3))
        
        return alerts


# Singleton instance
alerts_service = AlertsService()

