"""Teams router — manage team members per project."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/projects", tags=["Teams"])


@router.get(
    "/{project_id}/team",
    response_model=List[schemas.TeamMemberOut],
    summary="Get team members for a project",
)
async def get_team(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return all team members for a project (leads first, then alphabetical)."""
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return await crud.get_team(db, project_id)


@router.post(
    "/{project_id}/team",
    response_model=schemas.TeamMemberOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a team member to a project",
)
async def add_team_member(
    project_id: int,
    data: schemas.TeamMemberCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a new team member to a project."""
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return await crud.add_team_member(db, project_id, data)


@router.put(
    "/{project_id}/team/{member_id}",
    response_model=schemas.TeamMemberOut,
    summary="Update a team member",
)
async def update_team_member(
    project_id: int,
    member_id: int,
    data: schemas.TeamMemberUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a team member's role, allocation, or lead status."""
    member = await crud.update_team_member(db, member_id, data)
    if not member:
        raise HTTPException(status_code=404, detail=f"Team member {member_id} not found")
    return member


@router.delete(
    "/{project_id}/team/{member_id}",
    response_model=schemas.MessageResponse,
    summary="Remove a team member",
)
async def remove_team_member(
    project_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove a team member from a project."""
    deleted = await crud.remove_team_member(db, member_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Team member {member_id} not found")
    return {"message": f"Team member {member_id} removed successfully"}
