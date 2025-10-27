import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskBaseValidation(BaseModel):
    deadline: dt.datetime | None = None

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v):
        if v is None:
            return v

        now = dt.datetime.now(dt.timezone.utc)

        # Must be in future
        if v <= now:
            raise ValueError("Deadline must be in the future")

        # Optional: reasonable limit (e.g., not more than 10 years)
        max_future = now + dt.timedelta(days=365 * 10)
        if v > max_future:
            raise ValueError("Deadline cannot be more than 10 years in the future")

        return v


class TaskCreate(TaskBaseValidation):
    title: str
    description: str
    expected_duration_minutes: int = Field(gt=0)
    tips: list[str] = Field(default_factory=list)
    priority: int = Field(default=2, ge=0, le=4)  # 0 is highest priority


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

    @field_validator("tips", mode="before")
    @classmethod
    def handle_none_tips(cls, v):
        if v is None:
            return []
        return v


# LLM output (rename for clarity)
class TaskExtracted(BaseModel):
    title: str
    description: str
    expected_duration_minutes: int
    tips: list[str] = Field(default_factory=list)


# Only if you ingest raw text via JSON; for images/PDFs, use FastAPI UploadFile
class TaskExtractTextRequest(BaseModel):
    text: str
