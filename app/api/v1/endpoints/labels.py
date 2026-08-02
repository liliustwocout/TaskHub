from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.models.project import Project
from app.models.label import Label
from app.schemas.label import LabelCreate, LabelUpdate, LabelResponse
from app.api.v1.endpoints.workspaces import get_user_workspace_role

router = APIRouter()


@router.post("/projects/{project_id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    project_id: int,
    data: LabelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_res = await db.execute(select(Project).where(Project.id == project_id))
    project = project_res.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or EDITOR can create labels in this project",
        )

    label = Label(
        project_id=project_id,
        name=data.name,
        color=data.color,
    )
    db.add(label)
    await db.commit()
    await db.refresh(label)
    return label


@router.get("/projects/{project_id}/labels", response_model=List[LabelResponse])
async def list_project_labels(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_res = await db.execute(select(Project).where(Project.id == project_id))
    project = project_res.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    result = await db.execute(select(Label).where(Label.project_id == project_id))
    return result.scalars().all()


@router.patch("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: int,
    data: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    label_res = await db.execute(select(Label).where(Label.id == label_id))
    label = label_res.scalar_one_or_none()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == label.project_id))
    project = project_res.scalar_one_or_none()
    
    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or EDITOR can update labels",
        )

    if data.name is not None:
        label.name = data.name
    if data.color is not None:
        label.color = data.color

    await db.commit()
    await db.refresh(label)
    return label


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    label_res = await db.execute(select(Label).where(Label.id == label_id))
    label = label_res.scalar_one_or_none()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == label.project_id))
    project = project_res.scalar_one_or_none()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or EDITOR can delete labels",
        )

    await db.delete(label)
    await db.commit()
    return None
