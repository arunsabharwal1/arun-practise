"""Risks router — manage risk registry per project."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/projects", tags=["Risks"])


@router.get(
    "/{project_id}/risks",
    response_model=List[schemas.RiskEntryOut],
    summary="Get risk registry for a project",
)
async def get_risks(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return all risks for a project with computed risk_level (probability × impact matrix)."""
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return await crud.get_risks(db, project_id)


@router.post(
    "/{project_id}/risks",
    response_model=schemas.RiskEntryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new risk",
)
async def create_risk(
    project_id: int,
    data: schemas.RiskEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new risk entry. risk_level is auto-computed from probability × impact."""
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return await crud.create_risk(db, project_id, data)


@router.put(
    "/{project_id}/risks/{risk_id}",
    response_model=schemas.RiskEntryOut,
    summary="Update a risk entry",
)
async def update_risk(
    project_id: int,
    risk_id: int,
    data: schemas.RiskEntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a risk's probability, impact, status, or mitigation plan."""
    risk = await crud.update_risk(db, risk_id, data)
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk {risk_id} not found")
    return risk


@router.delete(
    "/{project_id}/risks/{risk_id}",
    response_model=schemas.MessageResponse,
    summary="Delete a risk entry",
)
async def delete_risk(
    project_id: int,
    risk_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a risk entry from the registry."""
    deleted = await crud.delete_risk(db, risk_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Risk {risk_id} not found")
    return {"message": f"Risk {risk_id} deleted successfully"}
