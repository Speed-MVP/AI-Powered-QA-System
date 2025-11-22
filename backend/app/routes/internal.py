"""
Internal API Endpoints
Legacy PolicyTemplate routes have been removed - use Phase 7 pipeline instead.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.middleware.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["internal"])


def require_internal_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Require internal access - only admins and QA managers, or service accounts.
    In production, this would also check for service tokens.
    """
    if current_user.role not in ["admin", "qa_manager"]:
        raise HTTPException(
            status_code=403,
            detail="Internal API access required"
        )
    return current_user
