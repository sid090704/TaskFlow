
from pydantic import BaseModel, ConfigDict, Field


class LabelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )


class LabelResponse(BaseModel):
    id: int
    project_id: int
    name: str
    color: str | None

    model_config = ConfigDict(from_attributes=True)
