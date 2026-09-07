"""
CRUD operations — pure database functions, separated from routing logic.
This clean separation makes it easy to add AI agents or background tasks
that call these functions directly without going through HTTP.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import Project, FinancialLog, TeamMember, RiskEntry, RiskStatus
from app import schemas


# ─── Project CRUD ─────────────────────────────────────────────────────────────

async def get_all_projects(db: AsyncSession) -> List[Project]:
    """Fetch all projects with counts for team and open risks."""
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.financial_logs),
            selectinload(Project.team_members),
            selectinload(Project.risks),
        )
        .order_by(Project.created_at.desc())
    )
    return result.scalars().all()


async def get_project(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Fetch a single project with all related data."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.financial_logs),
            selectinload(Project.team_members),
            selectinload(Project.risks),
        )
    )
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, data: schemas.ProjectCreate) -> Project:
    """Create a new project."""
    project = Project(**data.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession, project_id: int, data: schemas.ProjectUpdate
) -> Optional[Project]:
    """Update project fields. Returns None if not found."""
    project = await get_project(db, project_id)
    if not project:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.flush()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    """Delete a project. Returns True if deleted, False if not found."""
    project = await db.get(Project, project_id)
    if not project:
        return False
    await db.delete(project)
    return True


# ─── Financial CRUD ───────────────────────────────────────────────────────────

async def get_financials(db: AsyncSession, project_id: int) -> List[FinancialLog]:
    result = await db.execute(
        select(FinancialLog)
        .where(FinancialLog.project_id == project_id)
        .order_by(FinancialLog.logged_at.desc())
    )
    return result.scalars().all()


async def create_financial_log(
    db: AsyncSession, project_id: int, data: schemas.FinancialLogCreate
) -> FinancialLog:
    log = FinancialLog(project_id=project_id, **data.model_dump())
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def update_financial_log(
    db: AsyncSession, log_id: int, data: schemas.FinancialLogUpdate
) -> Optional[FinancialLog]:
    log = await db.get(FinancialLog, log_id)
    if not log:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    await db.flush()
    await db.refresh(log)
    return log


async def delete_financial_log(db: AsyncSession, log_id: int) -> bool:
    log = await db.get(FinancialLog, log_id)
    if not log:
        return False
    await db.delete(log)
    return True


# ─── Team CRUD ────────────────────────────────────────────────────────────────

async def get_team(db: AsyncSession, project_id: int) -> List[TeamMember]:
    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.project_id == project_id)
        .order_by(TeamMember.is_lead.desc(), TeamMember.name)
    )
    return result.scalars().all()


async def add_team_member(
    db: AsyncSession, project_id: int, data: schemas.TeamMemberCreate
) -> TeamMember:
    member = TeamMember(project_id=project_id, **data.model_dump())
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def update_team_member(
    db: AsyncSession, member_id: int, data: schemas.TeamMemberUpdate
) -> Optional[TeamMember]:
    member = await db.get(TeamMember, member_id)
    if not member:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    await db.flush()
    await db.refresh(member)
    return member


async def remove_team_member(db: AsyncSession, member_id: int) -> bool:
    member = await db.get(TeamMember, member_id)
    if not member:
        return False
    await db.delete(member)
    return True


# ─── Risk CRUD ────────────────────────────────────────────────────────────────

async def get_risks(db: AsyncSession, project_id: int) -> List[RiskEntry]:
    result = await db.execute(
        select(RiskEntry)
        .where(RiskEntry.project_id == project_id)
        .order_by(RiskEntry.identified_at.desc())
    )
    return result.scalars().all()


async def create_risk(
    db: AsyncSession, project_id: int, data: schemas.RiskEntryCreate
) -> RiskEntry:
    risk = RiskEntry(project_id=project_id, **data.model_dump())
    db.add(risk)
    await db.flush()
    await db.refresh(risk)
    return risk


async def update_risk(
    db: AsyncSession, risk_id: int, data: schemas.RiskEntryUpdate
) -> Optional[RiskEntry]:
    risk = await db.get(RiskEntry, risk_id)
    if not risk:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(risk, field, value)
    await db.flush()
    await db.refresh(risk)
    return risk


async def delete_risk(db: AsyncSession, risk_id: int) -> bool:
    risk = await db.get(RiskEntry, risk_id)
    if not risk:
        return False
    await db.delete(risk)
    return True
