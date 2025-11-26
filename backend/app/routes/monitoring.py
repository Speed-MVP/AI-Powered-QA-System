"""
Monitoring API Routes - Phase 10
Endpoints for metrics and alerts
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user
from app.services.monitoring import monitoring_service
from app.services.alerts import alerts_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/metrics")
async def get_metrics(
    days: int = Query(7, ge=1, le=30),
    company_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all monitoring metrics"""
    # Use current user's company if not specified
    target_company_id = company_id or current_user.company_id
    
    # Only admins can view other companies' metrics
    if company_id and company_id != current_user.company_id:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    metrics = monitoring_service.get_all_metrics(target_company_id, days)
    return metrics


@router.get("/metrics/compiler")
async def get_compiler_metrics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get compiler metrics"""
    stats = monitoring_service.get_compiler_stats(current_user.company_id, days)
    return stats


@router.get("/metrics/detection")
async def get_detection_metrics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detection engine metrics"""
    stats = monitoring_service.get_detection_stats(current_user.company_id, days)
    return stats


@router.get("/metrics/llm")
async def get_llm_metrics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get LLM evaluation metrics"""
    stats = monitoring_service.get_llm_stats(current_user.company_id, days)
    return stats


@router.get("/metrics/scoring")
async def get_scoring_metrics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scoring engine metrics"""
    stats = monitoring_service.get_scoring_stats(current_user.company_id, days)
    return stats


@router.get("/metrics/sandbox")
async def get_sandbox_metrics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sandbox metrics"""
    stats = monitoring_service.get_sandbox_stats(current_user.company_id, days)
    return stats


@router.get("/alerts")
async def get_alerts(
    days: int = Query(1, ge=1, le=7),
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active alerts"""
    alerts = alerts_service.check_all_alerts(current_user.company_id, days)
    
    # Filter by severity if specified
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    return {
        "alerts": [a.to_dict() for a in alerts],
        "total": len(alerts),
        "critical": len([a for a in alerts if a.severity == "critical"]),
        "warnings": len([a for a in alerts if a.severity == "warning"]),
        "info": len([a for a in alerts if a.severity == "info"])
    }

