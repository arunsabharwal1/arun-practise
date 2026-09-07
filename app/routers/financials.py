"""Financials router — log and update financial metrics per project."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/projects", tags=["Financials"])


@router.get(
    "/{project_id}/financials",
    response_model=List[schemas.FinancialLogOut],
    summary="Get financial logs for a project",
)
async def get_financials(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return all financial log entries for a project (latest first)."""
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return await crud.get_financials(db, project_id)


@router.post(
    "/{project_id}/financials",
    response_model=schemas.FinancialLogOut,
    status_code=status.HTTP_201_CREATED,
    summary="Log financial metrics for a project",
)
async def create_financial_log(
    project_id: int,
    data: schemas.FinancialLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a new financial log entry (budget, cost, revenue) to a project."""
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return await crud.create_financial_log(db, project_id, data)


@router.put(
    "/{project_id}/financials/{log_id}",
    response_model=schemas.FinancialLogOut,
    summary="Update a financial log entry",
)
async def update_financial_log(
    project_id: int,
    log_id: int,
    data: schemas.FinancialLogUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a specific financial log entry."""
    log = await crud.update_financial_log(db, log_id, data)
    if not log:
        raise HTTPException(status_code=404, detail=f"Financial log {log_id} not found")
    return log


@router.delete(
    "/{project_id}/financials/{log_id}",
    response_model=schemas.MessageResponse,
    summary="Delete a financial log entry",
)
async def delete_financial_log(
    project_id: int,
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific financial log entry."""
    deleted = await crud.delete_financial_log(db, log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Financial log {log_id} not found")
    return {"message": f"Financial log {log_id} deleted successfully"}
