"""Projects router — CRUD endpoints for projects."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=List[schemas.ProjectSummary], summary="List all projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    """Return a summary list of all projects with team size and open risk count."""
    projects = await crud.get_all_projects(db)
    summaries = []
    for p in projects:
        open_risks = sum(1 for r in p.risks if r.status.value == "open")
        summaries.append(
            schemas.ProjectSummary(
                id=p.id,
                name=p.name,
                client=p.client,
                status=p.status,
                start_date=p.start_date,
                end_date=p.end_date,
                team_size=len(p.team_members),
                open_risks=open_risks,
                created_at=p.created_at,
            )
        )
    return summaries


@router.get("/{project_id}", response_model=schemas.ProjectDetail, summary="Get project detail")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return full project detail including financials, team members, and risks."""
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@router.post("/", response_model=schemas.ProjectDetail, status_code=status.HTTP_201_CREATED, summary="Create project")
async def create_project(data: schemas.ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new project."""
    return await crud.create_project(db, data)


@router.put("/{project_id}", response_model=schemas.ProjectDetail, summary="Update project")
async def update_project(
    project_id: int, data: schemas.ProjectUpdate, db: AsyncSession = Depends(get_db)
):
    """Update project details or status."""
    project = await crud.update_project(db, project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@router.delete("/{project_id}", response_model=schemas.MessageResponse, summary="Delete project")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a project and all its related data (cascade)."""
    deleted = await crud.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return {"message": f"Project {project_id} deleted successfully"}
