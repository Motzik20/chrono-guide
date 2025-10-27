import datetime as dt

from pydantic import model_validator
from sqlalchemy import JSON, Column, DateTime, func
from sqlmodel import Field, SQLModel

from app.core.timezone import convert_model_datetimes_to_utc, now_utc


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="users.id", index=True)
    title: str
    description: str
    expected_duration_minutes: int = Field(
        ge=1, le=480, description="Duration between 1 minute and 8 hours (480 minutes)"
    )
    tips: list[str] | None = Field(default=None, sa_column=Column(JSON))
    deadline: dt.datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    priority: int = Field(
        default=2, nullable=False, ge=0, le=4
    )  # 0-4 range (0 is highest priority)
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
