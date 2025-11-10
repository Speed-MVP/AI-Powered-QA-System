from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.agent import AgentResponse
from app.routes.utils import ensure_supervisor, build_agent_response
from app.services.team_service import TeamService
import logging

router = APIRouter(prefix="/teams", tags=["teams"])
logger = logging.getLogger(__name__)
team_service = TeamService()


@router.get("/", response_model=List[TeamResponse])
async def list_teams(current_user: User = Depends(get_current_user)):
    """List all teams for the current user's company."""
    return team_service.get_teams(current_user.company_id)


@router.post("/", response_model=TeamResponse, status_code=201)
async def create_team(
    team_in: TeamCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new team. Supervisor+ only."""
    ensure_supervisor(current_user)
    try:
        return team_service.create_team(
            company_id=current_user.company_id,
            name=team_in.name,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a single team by ID."""
    team = team_service.get_team_by_id(team_id)
    if not team or team.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_in: TeamUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a team name. Supervisor+ only."""
    ensure_supervisor(current_user)
    if not team_in.name:
        raise HTTPException(status_code=400, detail="Team name is required")
    team = team_service.get_team_by_id(team_id)
    if not team or team.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Team not found")
    try:
        return team_service.update_team(team_id=team_id, name=team_in.name, updated_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Soft delete a team. Supervisor+ only."""
    ensure_supervisor(current_user)
    team = team_service.get_team_by_id(team_id)
    if not team or team.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Team not found")
    team_service.delete_team(team_id=team_id, deleted_by=current_user.id)
    return None


@router.get("/{team_id}/agents", response_model=List[AgentResponse])
async def list_team_agents(
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get all agents assigned to a team."""
    team = team_service.get_team_by_id(team_id)
    if not team or team.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Team not found")

    agents = team_service.get_team_agents(team_id)
    return [build_agent_response(agent) for agent in agents]
