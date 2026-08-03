import math
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.models.project import Project
from app.models.task import Task
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse
from app.api.v1.endpoints.workspaces import get_user_workspace_role

router = APIRouter()


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_res = await db.execute(select(Task).where(Task.id == task_id))
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == task.project_id))
    project = project_res.scalar_one()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    comment = Comment(
        task_id=task_id,
        author_id=current_user.id,
        content=data.content,
    )
    db.add(comment)
    await db.commit()

    res = await db.execute(
        select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment.id)
    )
    return res.scalar_one()


@router.get("/tasks/{task_id}/comments", response_model=List[CommentResponse])
async def list_task_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_res = await db.execute(select(Task).where(Task.id == task_id))
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == task.project_id))
    project = project_res.scalar_one()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    res = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.task_id == task_id)
        .order_by(Comment.created_at.asc())
    )
    return res.scalars().all()


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = res.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    task_res = await db.execute(select(Task).where(Task.id == comment.task_id))
    task = task_res.scalar_one()

    project_res = await db.execute(select(Project).where(Project.id == task.project_id))
    project = project_res.scalar_one()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)

    # Quyền xóa: Tác giả comment HOẶC Workspace OWNER
    if comment.author_id != current_user.id and role != WorkspaceRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only author or workspace owner can delete this comment",
        )

    await db.delete(comment)
    await db.commit()
    return None
