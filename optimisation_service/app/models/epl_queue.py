from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import UUID4, BaseModel, Field


class task_state(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLED = "cancelled"


class QueueElem(BaseModel):
    state: task_state = Field(
        examples=["queued", "running", "cancelled"],
        description="State of the task in the queue. Either queued, running or cancelled",
    )
    added_at: datetime = Field(examples=["2024-01-01T00:00:00Z"], description="Time at which task was added to queue.")


class QueueStatus(BaseModel):
    queue: dict[UUID4, QueueElem] = Field(
        examples=[{"805fb659-1cac-44f3-a1f9-85dc82178f53": "queued"}], description="Overview of queue elements."
    )
    service_uptime: timedelta = Field(description="Service uptime.")
