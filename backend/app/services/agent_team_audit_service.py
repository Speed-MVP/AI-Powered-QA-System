"""
Agent/Team Audit Service - Phase 1
Provides audit trail queries for agent and team changes.
"""

from app.database import SessionLocal
from app.models.agent_team import AgentTeamChange
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentTeamAuditService:
    """Provides audit trail queries for agent/team changes."""
    
    def get_changes(
        self,
        company_id: str,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AgentTeamChange]:
        """Query agent_team_changes with filters."""
        db = SessionLocal()
        try:
            query = db.query(AgentTeamChange).filter(
                AgentTeamChange.company_id == company_id
            )
            
            # Filter by agent_id (if entity is agent or membership)
            if agent_id:
                # For agent changes, entity_id matches agent_id
                # For membership changes, need to check membership's agent_id
                # For simplicity, we'll filter by entity_id for agent changes
                # and use a subquery for membership changes
                from app.models.agent_team import AgentTeamMembership
                
                # Get membership IDs for this agent
                memberships = db.query(AgentTeamMembership.id).filter(
                    AgentTeamMembership.agent_id == agent_id
                ).all()
                membership_ids = [m[0] for m in memberships]
                
                query = query.filter(
                    (AgentTeamChange.entity_id == agent_id) |
                    (AgentTeamChange.entity_id.in_(membership_ids))
                )
            
            # Filter by team_id
            if team_id:
                # For team changes, entity_id matches team_id
                # For membership changes, need to check membership's team_id
                from app.models.agent_team import AgentTeamMembership
                
                # Get membership IDs for this team
                memberships = db.query(AgentTeamMembership.id).filter(
                    AgentTeamMembership.team_id == team_id
                ).all()
                membership_ids = [m[0] for m in memberships]
                
                query = query.filter(
                    (AgentTeamChange.entity_id == team_id) |
                    (AgentTeamChange.entity_id.in_(membership_ids))
                )
            
            # Filter by entity_type
            if entity_type:
                query = query.filter(AgentTeamChange.entity_type == entity_type)
            
            # Filter by date range
            if date_from:
                query = query.filter(AgentTeamChange.changed_at >= date_from)
            
            if date_to:
                query = query.filter(AgentTeamChange.changed_at <= date_to)
            
            # Order by changed_at DESC and limit
            changes = query.order_by(
                AgentTeamChange.changed_at.desc()
            ).limit(limit).all()
            
            return changes
        finally:
            db.close()


