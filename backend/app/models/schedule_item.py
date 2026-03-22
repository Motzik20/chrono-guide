import datetime as dt
from typing import Any

from pydantic import model_validator
from sqlalchemy import Index, func
from sqlmodel import Column, DateTime, Field, SQLModel, String

from app.core.timezone import convert_model_datetimes_to_utc, now_utc


class ScheduleItem(SQLModel, table=True):
    __tablename__ = "schedule_items"  # type: ignore[assignment]
    __table_args__ = (
        Index("idx_schedule_items_user_start", "user_id", "start_time"),
        Index(
            "unique_external_id",
            "user_id",
            "source",
            "external_id",
            "connection_id",
            unique=True,
            postgresql_where=Column("external_id").isnot(None)
            & Column("connection_id").isnot(None),
        ),
    )
    # Unique constraint in migration for external values: UNIQUE (user_id, source, external_id, connection_id) WHERE external_id IS NOT NULL AND connection_id IS NOT NULL

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    task_id: int | None = Field(
        default=None, foreign_key="tasks.id", index=True, ondelete="CASCADE"
    )
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
    external_id: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )  # e.g. for storing the event id from an external calendar
    connection_id: int | None = Field(
        default=None,
        foreign_key="calendar_connections.id",
        nullable=True,
    )  # to link schedule items to a specific calendar connection if they were imported from an external calendar

    @model_validator(mode="before")
    @classmethod
    def convert_datetimes_to_utc(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Convert all datetime fields to UTC before validation."""
        return convert_model_datetimes_to_utc(data)
