from typing import List
from fastapi import HTTPException
from app.models.user import User, UserRole
from app.schemas.agent import AgentResponse, AgentTeamMembershipResponse


SUPERVISOR_ROLES = {UserRole.admin, UserRole.qa_manager}


def ensure_supervisor(current_user: User) -> None:
    """Raise if the user is not allowed to perform supervisor-level actions."""
    if current_user.role not in SUPERVISOR_ROLES:
        raise HTTPException(status_code=403, detail="Supervisor permissions required")


def build_agent_response(agent: User) -> AgentResponse:
    """Serialize a User model (agent) into AgentResponse with active memberships."""
    memberships: List[AgentTeamMembershipResponse] = []
    for membership in getattr(agent, "team_memberships", []) or []:
        if membership.deleted_at:
            continue
        team_name = membership.team.name if membership.team else None
        memberships.append(
            AgentTeamMembershipResponse(
                membership_id=membership.id,
                team_id=membership.team_id,
                team_name=team_name,
                role=membership.role,
            )
        )

    role_value = agent.role.value if hasattr(agent.role, "value") else agent.role
    return AgentResponse(
        id=agent.id,
        company_id=agent.company_id,
        email=agent.email,
        full_name=agent.full_name,
        role=role_value,
        is_active=agent.is_active,
        created_at=agent.created_at,
        team_memberships=memberships,
    )
