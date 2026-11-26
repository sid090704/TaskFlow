
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    id: int
    project_id: int
    task_id: int | None
    user_id: int | None
    action: str
    description: str
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
