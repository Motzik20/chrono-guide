import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
