import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.schedule_item import ScheduleItem


class ScheduleItemBase(BaseModel):
    start_time: dt.datetime | None = None
    end_time: dt.datetime | None = None
    title: str | None = None
    description: str | None = None
    source: str | None = Field(default="task")

    @field_validator("start_time", "end_time")
    @classmethod
    def times_must_be_future(cls, v: dt.datetime) -> dt.datetime:
        if v <= dt.datetime.now(dt.timezone.utc):
            raise ValueError("Schedule times must be in the future")
        return v

    @model_validator(mode="after")
    def end_after_start(self) -> "ScheduleItemBase":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("End time must be after start time")
        return self


class ScheduleItemCreate(ScheduleItemBase):
    task_id: int | None = None
    user_id: int


class ScheduleItemUpdate(ScheduleItemBase):
    task_id: int | None = None
    start_time: dt.datetime | None = None
    end_time: dt.datetime | None = None
    title: str | None = None
    description: str | None = None
    source: str | None = None


class ScheduleItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # replaces orm_mode in Pydantic v2
    id: int
    user_id: int
    task_id: int | None = None
    start_time: dt.datetime
    end_time: dt.datetime
    title: str | None = None
    description: str | None = None
    source: str = "task"
    created_at: dt.datetime
    updated_at: dt.datetime


class ScheduleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    task_id: int | None = None
    start_time: dt.datetime
    end_time: dt.datetime
    title: str | None = None
    description: str | None = None
    source: str = "task"
    created_at: dt.datetime
    updated_at: dt.datetime
    user_timezone: str

    @classmethod
    def from_model(
        cls, model: ScheduleItem, user_timezone: str
    ) -> "ScheduleItemResponse":
        return cls(
            id=model.id,  # type: ignore[attr-defined]
            user_id=model.user_id,
            task_id=model.task_id,
            start_time=model.start_time,
            end_time=model.end_time,
            title=model.title,
            description=model.description,
            source=model.source,
            created_at=model.created_at,
            updated_at=model.updated_at,
            user_timezone=user_timezone,
        )
