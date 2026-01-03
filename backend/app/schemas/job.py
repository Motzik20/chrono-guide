from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.schemas.task import IngestTaskResponse


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class CeleryJobBase(BaseModel):
    id: str
    status: JobStatus
    progress: float | None = None
    result: Any | None = None
    error: str | None = None


class IngestTaskJob(CeleryJobBase):
    result: IngestTaskResponse | None = None
