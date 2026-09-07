"""
SQLAlchemy ORM models for the Project Management application.

Models:
    - Project: Core project entity
    - FinancialLog: Cost and revenue tracking per project
    - TeamMember: Team assignment per project
    - RiskEntry: Risk registry per project
"""

import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, Date, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


# ─── Enumerations ────────────────────────────────────────────────────────────

class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(str, enum.Enum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


# ─── Models ──────────────────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    client = Column(String(200), nullable=True)
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.PLANNING, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    financial_logs = relationship("FinancialLog", back_populates="project", cascade="all, delete-orphan")
    team_members = relationship("TeamMember", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("RiskEntry", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project id={self.id} name={self.name!r} status={self.status}>"


class FinancialLog(Base):
    __tablename__ = "financial_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    budget = Column(Float, default=0.0, nullable=False)         # Total approved budget
    actual_cost = Column(Float, default=0.0, nullable=False)    # Spent so far
    revenue = Column(Float, default=0.0, nullable=False)        # Revenue earned/projected
    currency = Column(String(10), default="USD")
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)

    # Computed property
    @property
    def profit_margin(self) -> float:
        """Profit margin as a percentage: (revenue - cost) / revenue * 100"""
        if self.revenue == 0:
            return 0.0
        return round(((self.revenue - self.actual_cost) / self.revenue) * 100, 2)

    @property
    def budget_utilization(self) -> float:
        """How much of budget has been spent: cost / budget * 100"""
        if self.budget == 0:
            return 0.0
        return round((self.actual_cost / self.budget) * 100, 2)

    # Relationship
    project = relationship("Project", back_populates="financial_logs")

    def __repr__(self):
        return f"<FinancialLog project_id={self.project_id} budget={self.budget} cost={self.actual_cost}>"


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    role = Column(String(100), nullable=False)
    email = Column(String(200), nullable=True)
    allocation_percentage = Column(Float, default=100.0)  # % of time on this project
    is_lead = Column(Boolean, default=False)
    joined_at = Column(Date, nullable=True)

    # Relationship
    project = relationship("Project", back_populates="team_members")

    def __repr__(self):
        return f"<TeamMember name={self.name!r} role={self.role!r} project_id={self.project_id}>"


class RiskEntry(Base):
    __tablename__ = "risk_entries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    probability = Column(SAEnum(RiskLevel), nullable=False)     # Likelihood of occurrence
    impact = Column(SAEnum(RiskLevel), nullable=False)          # Business impact if it occurs
    status = Column(SAEnum(RiskStatus), default=RiskStatus.OPEN)
    mitigation_plan = Column(Text, nullable=True)
    owner = Column(String(200), nullable=True)
    identified_at = Column(DateTime, default=datetime.utcnow)

    # Computed risk level (probability × impact matrix)
    @property
    def risk_level(self) -> str:
        """Compute overall risk level from probability and impact."""
        matrix = {
            ("low", "low"): "low",
            ("low", "medium"): "low",
            ("low", "high"): "medium",
            ("low", "critical"): "medium",
            ("medium", "low"): "low",
            ("medium", "medium"): "medium",
            ("medium", "high"): "high",
            ("medium", "critical"): "critical",
            ("high", "low"): "medium",
            ("high", "medium"): "high",
            ("high", "high"): "critical",
            ("high", "critical"): "critical",
            ("critical", "low"): "medium",
            ("critical", "medium"): "high",
            ("critical", "high"): "critical",
            ("critical", "critical"): "critical",
        }
        return matrix.get((self.probability.value, self.impact.value), "medium")

    # Relationship
    project = relationship("Project", back_populates="risks")

    def __repr__(self):
        return f"<RiskEntry title={self.title!r} level={self.risk_level} project_id={self.project_id}>"
