from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict
from app.models.task import TaskStatus, TaskPriority
from app.schemas.label import LabelResponse


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    assignee_id: int | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    assignee_id: int | None = None
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None = None
    created_by: int
    created_at: datetime
    labels: List[LabelResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TaskPaginatedResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    limit: int
    total_pages: int
