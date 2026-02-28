import datetime as dt
from typing import Any

from pydantic import model_validator
from sqlalchemy import Text, func
from sqlmodel import Column, DateTime, Field, SQLModel, String, Boolean

from app.core.timezone import convert_model_datetimes_to_utc, now_utc


class CalendarConnection(SQLModel, table=True):
    __tablename__ = "calendar_connections"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    connection_type: str = Field(sa_column=Column(String(30), nullable=False)) # e.g., "ics_url", "caldav_basic" and other types of connections
    label: str = Field(sa_column=Column(String(100), nullable=False)) # human readable name that can be assigne in the app
    calendar_url: str = Field(sa_column=Column(Text, nullable=False))
    username: str | None = Field(sa_column=Column(String(255), nullable=True))
    key_id: str | None = Field(sa_column=Column(String(20), nullable=True))
    secret: str | None = Field(sa_column=Column(Text, nullable=True))
    last_error: str | None = Field(sa_column=Column(Text, nullable=True))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False)) # Disable connection without deleting it
    last_synced_at: dt.datetime = Field(
      default_factory=now_utc,
      sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    last_error_at: dt.datetime | None = Field(
      sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    secret_updated_at: dt.datetime | None = Field(
      sa_column=Column(DateTime(timezone=True), nullable=True),
    )
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
    def convert_datetimes_to_utc(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Convert all datetime fields to UTC before validation."""
        return convert_model_datetimes_to_utc(data)
