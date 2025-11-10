"""
Agent Service - Phase 1
Handles agent CRUD operations and agent-team membership.
"""

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.agent_team import AgentTeamMembership
from app.models.team import Team
from typing import List, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentService:
    """Handles agent CRUD and agent-team membership."""
    
    def __init__(self):
        self.team_service = None  # Will be set to avoid circular import
    
    def _get_team_service(self):
        """Lazy import to avoid circular dependency."""
        if self.team_service is None:
            from app.services.team_service import TeamService
            self.team_service = TeamService()
        return self.team_service
    
    def create_agent(
        self,
        company_id: str,
        email: str,
        full_name: str,
        team_id: Optional[str] = None,
        created_by: str = None
    ) -> User:
        """Create a new agent. This is a user with role 'agent'."""
        db = SessionLocal()
        try:
            # Check if user with this email already exists
            existing = db.query(User).filter(
                User.email == email,
                User.deleted_at.is_(None)
            ).first()
            
            if existing:
                raise ValueError(f"User with email '{email}' already exists")
            
            # Create user record with role='agent' (using reviewer role for now, can be extended)
            # Note: UserRole enum doesn't have 'agent' yet, using reviewer as placeholder
            agent = User(
                id=str(uuid.uuid4()),
                company_id=company_id,
                email=email,
                full_name=full_name,
                role=UserRole.reviewer,  # TODO: Add 'agent' role to UserRole enum if needed
                created_by=created_by,
                updated_by=created_by
            )
            db.add(agent)
            db.flush()
            
            # If team_id provided, add to agent_team_memberships
            if team_id:
                # Verify team exists
                team = db.query(Team).filter(
                    Team.id == team_id,
                    Team.deleted_at.is_(None)
                ).first()
                if not team:
                    raise ValueError(f"Team {team_id} not found")
                
                self.assign_agent_to_team(
                    agent_id=agent.id,
                    team_id=team_id,
                    created_by=created_by or agent.id
                )
            
            # Log change
            self._log_change(
                db=db,
                entity_type='agent',
                entity_id=agent.id,
                change_type='created',
                field_name='email',
                old_value=None,
                new_value=email,
                changed_by=created_by or agent.id,
                company_id=company_id
            )
            
            db.commit()
            return agent
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating agent: {e}")
            raise
        finally:
            db.close()
    
    def get_agents(self, company_id: str, team_id: Optional[str] = None) -> List[User]:
        """Get agents, optionally filtered by team."""
        db = SessionLocal()
        try:
            query = db.query(User).filter(
                User.company_id == company_id,
                User.deleted_at.is_(None)
            )
            
            # Filter by team if provided
            if team_id:
                from app.models.agent_team import AgentTeamMembership
                memberships = db.query(AgentTeamMembership).filter(
                    AgentTeamMembership.team_id == team_id,
                    AgentTeamMembership.deleted_at.is_(None)
                ).all()
                agent_ids = [m.agent_id for m in memberships]
                if agent_ids:
                    query = query.filter(User.id.in_(agent_ids))
                else:
                    return []  # No agents in this team
            
            agents = query.order_by(User.full_name).all()
            return agents
        finally:
            db.close()
    
    def get_agent_by_id(self, agent_id: str) -> Optional[User]:
        """Get single agent by ID."""
        db = SessionLocal()
        try:
            agent = db.query(User).filter(
                User.id == agent_id,
                User.deleted_at.is_(None)
            ).first()
            return agent
        finally:
            db.close()
    
    def update_agent(
        self,
        agent_id: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        updated_by: str = None
    ) -> User:
        """Update agent details. Log changes."""
        db = SessionLocal()
        try:
            agent = db.query(User).filter(
                User.id == agent_id,
                User.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Track changes for audit
            changes = []
            
            if email and email != agent.email:
                old_email = agent.email
                agent.email = email
                changes.append(('email', old_email, email))
            
            if full_name and full_name != agent.full_name:
                old_name = agent.full_name
                agent.full_name = full_name
                changes.append(('full_name', old_name, full_name))
            
            if changes:
                agent.updated_by = updated_by or agent.id
                agent.updated_at = datetime.utcnow()
                
                # Log each change
                for field_name, old_value, new_value in changes:
                    self._log_change(
                        db=db,
                        entity_type='agent',
                        entity_id=agent_id,
                        change_type='updated',
                        field_name=field_name,
                        old_value=old_value,
                        new_value=new_value,
                        changed_by=updated_by or agent.id,
                        company_id=agent.company_id
                    )
                
                db.commit()
                db.refresh(agent)
            
            return agent
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating agent: {e}")
            raise
        finally:
            db.close()
    
    def delete_agent(self, agent_id: str, deleted_by: str) -> None:
        """Soft delete agent."""
        db = SessionLocal()
        try:
            agent = db.query(User).filter(
                User.id == agent_id,
                User.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent.deleted_at = datetime.utcnow()
            agent.updated_by = deleted_by
            agent.updated_at = datetime.utcnow()
            
            # Log change
            self._log_change(
                db=db,
                entity_type='agent',
                entity_id=agent_id,
                change_type='deleted',
                field_name=None,
                old_value=agent.email,
                new_value=None,
                changed_by=deleted_by,
                company_id=agent.company_id
            )
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting agent: {e}")
            raise
        finally:
            db.close()
    
    def assign_agent_to_team(self, agent_id: str, team_id: str, created_by: str) -> AgentTeamMembership:
        """Add agent to team (create membership)."""
        db = SessionLocal()
        try:
            # Check if already assigned
            existing = db.query(AgentTeamMembership).filter(
                AgentTeamMembership.agent_id == agent_id,
                AgentTeamMembership.team_id == team_id,
                AgentTeamMembership.deleted_at.is_(None)
            ).first()
            
            if existing:
                raise ValueError(f"Agent {agent_id} is already assigned to team {team_id}")
            
            # Verify agent and team exist
            agent = db.query(User).filter(User.id == agent_id).first()
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError(f"Team {team_id} not found")
            
            # Create membership
            membership = AgentTeamMembership(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                team_id=team_id,
                created_by=created_by
            )
            db.add(membership)
            db.flush()
            
            # Log change
            self._log_change(
                db=db,
                entity_type='membership',
                entity_id=membership.id,
                change_type='created',
                field_name='team_id',
                old_value=None,
                new_value=team_id,
                changed_by=created_by,
                company_id=agent.company_id
            )
            
            db.commit()
            return membership
        except Exception as e:
            db.rollback()
            logger.error(f"Error assigning agent to team: {e}")
            raise
        finally:
            db.close()
    
    def remove_agent_from_team(self, agent_id: str, team_id: str, deleted_by: str) -> None:
        """Remove agent from team (soft delete membership)."""
        db = SessionLocal()
        try:
            membership = db.query(AgentTeamMembership).filter(
                AgentTeamMembership.agent_id == agent_id,
                AgentTeamMembership.team_id == team_id,
                AgentTeamMembership.deleted_at.is_(None)
            ).first()
            
            if not membership:
                raise ValueError(f"Membership not found for agent {agent_id} and team {team_id}")
            
            # Get agent for company_id
            agent = db.query(User).filter(User.id == agent_id).first()
            
            membership.deleted_at = datetime.utcnow()
            membership.updated_at = datetime.utcnow()
            
            # Log change
            self._log_change(
                db=db,
                entity_type='membership',
                entity_id=membership.id,
                change_type='deleted',
                field_name='team_id',
                old_value=team_id,
                new_value=None,
                changed_by=deleted_by,
                company_id=agent.company_id if agent else None
            )
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing agent from team: {e}")
            raise
        finally:
            db.close()
    
    def _log_change(
        self,
        db,
        entity_type: str,
        entity_id: str,
        change_type: str,
        field_name: Optional[str],
        old_value: Optional[str],
        new_value: Optional[str],
        changed_by: str,
        company_id: Optional[str]
    ) -> None:
        """Generic audit logging."""
        from app.models.agent_team import AgentTeamChange
        
        if not company_id:
            return  # Skip if no company_id
        
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


