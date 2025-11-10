from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.schemas.audit import AgentAuditLogResponse
from app.routes.utils import ensure_supervisor, build_agent_response
from app.services.agent_service import AgentService
from app.services.team_service import TeamService
from app.services.agent_team_audit_service import AgentTeamAuditService
import logging

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)
agent_service = AgentService()
team_service = TeamService()
audit_service = AgentTeamAuditService()


def _validate_team_access(team_id: Optional[str], current_user: User) -> Optional[str]:
    """Ensure the referenced team exists and belongs to the user's company."""
    if not team_id:
        return None
    team = team_service.get_team_by_id(team_id)
    if not team or team.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Team not found")
    return team.id


def _load_agent_or_404(agent_id: str, current_user: User):
    agent = agent_service.get_agent_by_id(agent_id)
    if not agent or agent.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    team_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List agents for the company, optionally filtered by team."""
    if team_id:
        _validate_team_access(team_id, current_user)
    agents = agent_service.get_agents(company_id=current_user.company_id, team_id=team_id)
    return [build_agent_response(agent) for agent in agents]


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_in: AgentCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a single agent. Supervisor+ only."""
    ensure_supervisor(current_user)
    team_id = _validate_team_access(agent_in.team_id, current_user)
    try:
        agent = agent_service.create_agent(
            company_id=current_user.company_id,
            email=agent_in.email,
            full_name=agent_in.full_name,
            team_id=team_id,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Reload with memberships for serialization
    fresh_agent = agent_service.get_agent_by_id(agent.id)
    return build_agent_response(fresh_agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get agent details."""
    agent = _load_agent_or_404(agent_id, current_user)
    return build_agent_response(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_in: AgentUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update agent details (Supervisor+ only)."""
    ensure_supervisor(current_user)
    agent = _load_agent_or_404(agent_id, current_user)
    try:
        agent_service.update_agent(
            agent_id=agent_id,
            email=agent_in.email,
            full_name=agent_in.full_name,
            updated_by=current_user.id,
        )
        if agent_in.team_id:
            team_id = _validate_team_access(agent_in.team_id, current_user)
            try:
                agent_service.assign_agent_to_team(
                    agent_id=agent_id,
                    team_id=team_id,
                    created_by=current_user.id,
                )
            except ValueError as exc:
                # If already assigned, ignore; otherwise surface error
                if "already assigned" not in str(exc).lower():
                    raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    fresh_agent = agent_service.get_agent_by_id(agent_id)
    return build_agent_response(fresh_agent)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
):
    """Soft delete an agent (Supervisor+ only)."""
    ensure_supervisor(current_user)
    _load_agent_or_404(agent_id, current_user)
    agent_service.delete_agent(agent_id=agent_id, deleted_by=current_user.id)
    return None


@router.get("/audit-log", response_model=List[AgentAuditLogResponse])
async def get_audit_log(
    agent_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None, description="agent|team|membership"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    """Get immutable audit trail (Supervisor+ only)."""
    ensure_supervisor(current_user)
    if team_id:
        _validate_team_access(team_id, current_user)
    if agent_id:
        _load_agent_or_404(agent_id, current_user)

    changes = audit_service.get_changes(
        company_id=current_user.company_id,
        agent_id=agent_id,
        team_id=team_id,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return changes
