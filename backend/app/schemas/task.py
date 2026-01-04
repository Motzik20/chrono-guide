import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import Task


class TaskBaseValidation(BaseModel):
    deadline: dt.datetime | None = None

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: dt.datetime | None) -> dt.datetime | None:
        if v is None:
            return v

        now = dt.datetime.now(dt.timezone.utc)

        if v <= now:
            raise ValueError("Deadline must be in the future")

        max_future = now + dt.timedelta(days=365 * 10)
        if v > max_future:
            raise ValueError("Deadline cannot be more than 10 years in the future")

        return v


class TaskCreate(TaskBaseValidation):
    title: str
    description: str
    expected_duration_minutes: int = Field(gt=0)
    tips: list[str] = Field(default_factory=list)
    priority: int = Field(default=2, ge=0, le=4)


class TaskUpdate(TaskBaseValidation):
    title: str | None = None
    description: str | None = None
    expected_duration_minutes: int | None = Field(default=None, gt=0)
    tips: list[str] | None = None
    priority: int | None = Field(default=None, ge=0, le=4)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # replaces orm_mode in Pydantic v2
    id: int
    user_id: int
    title: str
    description: str
    expected_duration_minutes: int
    tips: list[str] | None = None
    deadline: dt.datetime | None = None
    priority: int
    created_at: dt.datetime
    updated_at: dt.datetime
    scheduled_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    committed_at: dt.datetime | None = None
    user_timezone: str

    @field_validator("tips", mode="before")
    @classmethod
    def handle_none_tips(cls, v: list[str] | None) -> list[str]:
        if v is None:
            return []
        return v

    @classmethod
    def from_model(cls, model: Task, user_timezone: str) -> "TaskRead":
        return cls(
            id=model.id,  # type: ignore[attr-defined]
            user_id=model.user_id,
            title=model.title,
            description=model.description,
            expected_duration_minutes=model.expected_duration_minutes,
            tips=model.tips,
            deadline=model.deadline,
            priority=model.priority,
            created_at=model.created_at,
            updated_at=model.updated_at,
            scheduled_at=model.scheduled_at,
            completed_at=model.completed_at,
            committed_at=model.committed_at,
            user_timezone=user_timezone,
        )


class TasksDelete(BaseModel):
    task_ids: list[int]


# LLM output (rename for clarity)
class TaskExtracted(BaseModel):
    title: str
    description: str
    expected_duration_minutes: int
    tips: list[str] = Field(default_factory=list)


class TaskDraft(BaseModel):
    """Result from AI analysis of an file or text- extracted task information"""

    title: str
    description: str
    expected_duration_minutes: int = Field(
        ge=1, le=480, description="Duration between 1 minute and 8 hours (480 minutes)"
    )
    tips: list[str] = Field(default_factory=list)


class FileAnalysisRequest(BaseModel):
    file_content: bytes
    content_type: str
    language: str


class TextAnalysisRequest(BaseModel):
    text: str


class TasksCreateResponse(BaseModel):
    task_ids: list[int]
    created_count: int


class TaskCreateResponse(BaseModel):
    task_id: int
    created: bool


class IngestTaskResponse(BaseModel):
    draft_ids: list[int]
    created_count: int


class JobResponse(BaseModel):
    job_id: str
    status: str = "processing"
