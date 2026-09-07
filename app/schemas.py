"""
Pydantic v2 schemas for request/response validation.

Naming convention:
    - <Model>Create  → request body for POST
    - <Model>Update  → request body for PUT (all fields optional)
    - <Model>Out     → response schema (what API returns)
    - <Model>Detail  → full nested response (includes relationships)
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator, computed_field
from app.models import ProjectStatus, RiskLevel, RiskStatus


# ─── Financial Schemas ────────────────────────────────────────────────────────

class FinancialLogCreate(BaseModel):
    budget: float = 0.0
    actual_cost: float = 0.0
    revenue: float = 0.0
    currency: str = "USD"
    notes: Optional[str] = None


class FinancialLogUpdate(BaseModel):
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    revenue: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


class FinancialLogOut(BaseModel):
    id: int
    project_id: int
    budget: float
    actual_cost: float
    revenue: float
    profit_margin: float
    budget_utilization: float
    currency: str
    notes: Optional[str]
    logged_at: datetime

    model_config = {"from_attributes": True}


# ─── Team Member Schemas ──────────────────────────────────────────────────────

class TeamMemberCreate(BaseModel):
    name: str
    role: str
    email: Optional[str] = None
    allocation_percentage: float = 100.0
    is_lead: bool = False
    joined_at: Optional[date] = None


class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    allocation_percentage: Optional[float] = None
    is_lead: Optional[bool] = None
    joined_at: Optional[date] = None


class TeamMemberOut(BaseModel):
    id: int
    project_id: int
    name: str
    role: str
    email: Optional[str]
    allocation_percentage: float
    is_lead: bool
    joined_at: Optional[date]

    model_config = {"from_attributes": True}


# ─── Risk Schemas ─────────────────────────────────────────────────────────────

class RiskEntryCreate(BaseModel):
    title: str
    description: Optional[str] = None
    probability: RiskLevel
    impact: RiskLevel
    status: RiskStatus = RiskStatus.OPEN
    mitigation_plan: Optional[str] = None
    owner: Optional[str] = None


class RiskEntryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    probability: Optional[RiskLevel] = None
    impact: Optional[RiskLevel] = None
    status: Optional[RiskStatus] = None
    mitigation_plan: Optional[str] = None
    owner: Optional[str] = None


class RiskEntryOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    probability: RiskLevel
    impact: RiskLevel
    risk_level: str          # Computed from matrix
    status: RiskStatus
    mitigation_plan: Optional[str]
    owner: Optional[str]
    identified_at: datetime

    model_config = {"from_attributes": True}


# ─── Project Schemas ──────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    client: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client: Optional[str] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectSummary(BaseModel):
    """Lightweight project summary for list endpoint."""
    id: int
    name: str
    client: Optional[str]
    status: ProjectStatus
    start_date: Optional[date]
    end_date: Optional[date]
    team_size: int = 0
    open_risks: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(BaseModel):
    """Full project detail including all relationships."""
    id: int
    name: str
    description: Optional[str]
    client: Optional[str]
    status: ProjectStatus
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    financial_logs: List[FinancialLogOut] = []
    team_members: List[TeamMemberOut] = []
    risks: List[RiskEntryOut] = []

    model_config = {"from_attributes": True}


# ─── Generic Responses ────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
