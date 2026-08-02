from pydantic import BaseModel, ConfigDict


class LabelCreate(BaseModel):
    name: str
    color: str = "#808080"


class LabelUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class LabelResponse(BaseModel):
    id: int
    project_id: int
    name: str
    color: str

    model_config = ConfigDict(from_attributes=True)
