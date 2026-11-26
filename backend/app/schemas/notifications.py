
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    project_id: int | None
    task_id: int | None
    actor_id: int | None
    notification_type: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
