from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: str | None = None
    status: ProjectStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
