"""Team and TeamMember models for team budget management."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Team(Base):
    """Team model for managing shared monthly budgets."""

    __tablename__ = "teams"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    monthly_budget_usd = Column(Numeric(10, 2), nullable=False)
    monthly_reset_policy = Column(String(20), nullable=False, server_default="reset")
    daily_limit_enabled = Column(Boolean, default=True, nullable=False)
    monthly_budget_start = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User")
    members = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name})>"


class TeamMember(Base):
    """Join table linking tokens to teams with allocation amounts."""

    __tablename__ = "team_members"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("api_tokens.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    allocated_usd = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    team = relationship("Team", back_populates="members")
    token = relationship("APIToken", back_populates="team_membership")

    def __repr__(self) -> str:
        return (
            f"<TeamMember(team_id={self.team_id}, "
            f"token_id={self.token_id}, allocated={self.allocated_usd})>"
        )
