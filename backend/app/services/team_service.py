"""
Team Service - Phase 1
Handles team CRUD operations and audit logging.
"""

from app.database import SessionLocal
from app.models.team import Team
from app.models.agent_team import AgentTeamChange, AgentTeamMembership
from app.models.user import User
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class TeamService:
    """Handles team CRUD and audit logging."""
    
    def create_team(self, company_id: str, name: str, created_by: str) -> Team:
        """Create a new team. Log to agent_team_changes."""
        db = SessionLocal()
        try:
            # Check if team name already exists for this company
            existing = db.query(Team).filter(
                Team.company_id == company_id,
                Team.name == name,
                Team.deleted_at.is_(None)
            ).first()
            
            if existing:
                raise ValueError(f"Team '{name}' already exists for this company")
            
            # Create team
            team = Team(
                id=str(uuid.uuid4()),
                company_id=company_id,
                name=name,
                created_by=created_by,
                updated_by=created_by
            )
            db.add(team)
            db.flush()  # Get the ID
            
            # Log change
            self.log_change(
                db=db,
                entity_type='team',
                entity_id=team.id,
                change_type='created',
                field_name='name',
                old_value=None,
                new_value=name,
                changed_by=created_by,
                company_id=company_id
            )
            
            db.commit()
            db.refresh(team)  # Refresh to ensure object is attached for serialization
            return team
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating team: {e}")
            raise
        finally:
            db.close()
    
    def get_teams(self, company_id: str) -> List[Team]:
        """Get all teams for a company (exclude deleted)."""
        db = SessionLocal()
        try:
            teams = db.query(Team).filter(
                Team.company_id == company_id,
                Team.deleted_at.is_(None)
            ).order_by(Team.name).all()
            return teams
        finally:
            db.close()
    
    def get_team_by_id(self, team_id: str) -> Optional[Team]:
        """Get single team by ID."""
        db = SessionLocal()
        try:
            team = db.query(Team).filter(
                Team.id == team_id,
                Team.deleted_at.is_(None)
            ).first()
            return team
        finally:
            db.close()
    
    def update_team(self, team_id: str, name: str, updated_by: str) -> Team:
        """Update team. Log old/new values to audit trail."""
        db = SessionLocal()
        try:
            team = db.query(Team).filter(
                Team.id == team_id,
                Team.deleted_at.is_(None)
            ).first()
            
            if not team:
                raise ValueError(f"Team {team_id} not found")
            
            old_name = team.name
            team.name = name
            team.updated_by = updated_by
            team.updated_at = datetime.utcnow()
            
            # Log change
            self.log_change(
                db=db,
                entity_type='team',
                entity_id=team_id,
                change_type='updated',
                field_name='name',
                old_value=old_name,
                new_value=name,
                changed_by=updated_by,
                company_id=team.company_id
            )
            
            db.commit()
            db.refresh(team)
            return team
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating team: {e}")
            raise
        finally:
            db.close()
    
    def delete_team(self, team_id: str, deleted_by: str) -> None:
        """Soft delete team (set deleted_at)."""
        db = SessionLocal()
        try:
            team = db.query(Team).filter(
                Team.id == team_id,
                Team.deleted_at.is_(None)
            ).first()
            
            if not team:
                raise ValueError(f"Team {team_id} not found")
            
            team.deleted_at = datetime.utcnow()
            team.updated_by = deleted_by
            team.updated_at = datetime.utcnow()
            
            # Log change
            self.log_change(
                db=db,
                entity_type='team',
                entity_id=team_id,
                change_type='deleted',
                field_name=None,
                old_value=team.name,
                new_value=None,
                changed_by=deleted_by,
                company_id=team.company_id
            )
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting team: {e}")
            raise
        finally:
            db.close()
    
    def get_team_agents(self, team_id: str) -> List[User]:
        """Get all agents in a team (via agent_team_memberships)."""
        db = SessionLocal()
        try:
            memberships = db.query(AgentTeamMembership).filter(
                AgentTeamMembership.team_id == team_id,
                AgentTeamMembership.deleted_at.is_(None)
            ).all()
            
            agent_ids = [m.agent_id for m in memberships]
            if not agent_ids:
                return []
            
            agents = db.query(User).options(
                joinedload(User.team_memberships).joinedload(AgentTeamMembership.team)
            ).filter(
                User.id.in_(agent_ids),
                User.deleted_at.is_(None)
            ).all()
            
            return agents
        finally:
            db.close()
    
    def log_change(
        self,
        db,
        entity_type: str,
        entity_id: str,
        change_type: str,
        field_name: Optional[str],
        old_value: Optional[str],
        new_value: Optional[str],
        changed_by: str,
        company_id: str
    ) -> None:
        """Generic audit logging. Reusable for agent changes too."""
        change = AgentTeamChange(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            company_id=company_id
        )
        db.add(change)


