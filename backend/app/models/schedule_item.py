import datetime as dt

from pydantic import model_validator
from sqlalchemy import Index, func
from sqlmodel import Column, DateTime, Field, SQLModel, String

from app.core.timezone import convert_model_datetimes_to_utc, now_utc


class ScheduleItem(SQLModel, table=True):
    __tablename__ = "schedule_items"
    __table_args__ = (Index("idx_schedule_items_user_start", "user_id", "start_time"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="users.id")
    task_id: int | None = Field(default=None, foreign_key="tasks.id", index=True)
    start_time: dt.datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    end_time: dt.datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    source: str = Field(default="task", sa_column=Column(String(20), nullable=False))
    title: str | None = Field(default=None, nullable=True)
    description: str | None = Field(default=None, nullable=True)
    created_at: dt.datetime = Field(
        default_factory=now_utc,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: dt.datetime = Field(
        default_factory=now_utc,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    @model_validator(mode="before")
    @classmethod
    def convert_datetimes_to_utc(cls, data):
        """Convert all datetime fields to UTC before validation."""
        if isinstance(data, dict):
            return convert_model_datetimes_to_utc(data)
        return data
