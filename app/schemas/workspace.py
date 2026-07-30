from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.workspace import WorkspaceRole
from app.schemas.user import UserResponse


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceUpdate(BaseModel):
    name: str


class WorkspaceMemberAdd(BaseModel):
    user_id: int
    role: WorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberUpdate(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: WorkspaceRole
    created_at: datetime
    user: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime
    my_role: WorkspaceRole | None = None

    model_config = ConfigDict(from_attributes=True)
