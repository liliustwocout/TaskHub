from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.label import Label
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.api.v1.endpoints.workspaces import get_user_workspace_role

router = APIRouter()


async def validate_workspace_member(db: AsyncSession, workspace_id: int, user_id: int) -> bool:
    role = await get_user_workspace_role(db, workspace_id, user_id)
    return role is not None


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    data: TaskCreate,
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
            detail="Only OWNER or EDITOR can create tasks in this project",
        )

    if data.assignee_id is not None:
        is_member = await validate_workspace_member(db, project.workspace_id, data.assignee_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee is not a member of this workspace",
            )

    task = Task(
        project_id=project_id,
        assignee_id=data.assignee_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
        created_by=current_user.id,
    )
    db.add(task)
    await db.commit()

    # Query back with labels loaded
    res = await db.execute(
        select(Task).options(selectinload(Task.labels)).where(Task.id == task.id)
    )
    return res.scalar_one()


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
async def list_project_tasks(
    project_id: int,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority_filter: Optional[TaskPriority] = Query(None, alias="priority"),
    assignee_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
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

    stmt = select(Task).options(selectinload(Task.labels)).where(Task.project_id == project_id)

    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)
    if priority_filter is not None:
        stmt = stmt.where(Task.priority == priority_filter)
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
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
            detail="You do not have access to this task",
        )

    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == task.project_id))
    project = project_res.scalar_one()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or EDITOR can edit task",
        )

    if data.assignee_id is not None:
        is_member = await validate_workspace_member(db, project.workspace_id, data.assignee_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee is not a member of this workspace",
            )
        task.assignee_id = data.assignee_id

    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.status is not None:
        task.status = data.status
    if data.priority is not None:
        task.priority = data.priority
    if data.due_date is not None:
        task.due_date = data.due_date

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(Task).where(Task.id == task_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == task.project_id))
    project = project_res.scalar_one()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or EDITOR can delete task",
        )

    await db.delete(task)
    await db.commit()
    return None


@router.post("/tasks/{task_id}/labels/{label_id}", response_model=TaskResponse)
async def add_label_to_task(
    task_id: int,
    label_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == task.project_id))
    project = project_res.scalar_one()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or EDITOR can manage task labels",
        )

    label_res = await db.execute(select(Label).where(Label.id == label_id))
    label = label_res.scalar_one_or_none()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    if label.project_id != task.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Label does not belong to the same project as the task",
        )

    if label not in task.labels:
        task.labels.append(label)
        await db.commit()
        await db.refresh(task)

    return task


@router.delete("/tasks/{task_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_label_from_task(
    task_id: int,
    label_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    project_res = await db.execute(select(Project).where(Project.id == task.project_id))
    project = project_res.scalar_one()

    role = await get_user_workspace_role(db, project.workspace_id, current_user.id)
    if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or EDITOR can manage task labels",
        )

    label_res = await db.execute(select(Label).where(Label.id == label_id))
    label = label_res.scalar_one_or_none()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    if label in task.labels:
        task.labels.remove(label)
        await db.commit()

    return None
