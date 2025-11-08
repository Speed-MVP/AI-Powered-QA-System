from app.models.user import User, UserRole
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Callable


def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def check_role(current_user: User):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role


def require_company_access(company_id: str, current_user: User):
    """Check if user has access to company"""
    if current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

