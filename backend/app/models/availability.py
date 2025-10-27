import datetime as dt

from pydantic import model_validator
from sqlalchemy import UniqueConstraint, func
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, String, Time

from app.core.timezone import convert_model_datetimes_to_utc, now_utc


class WeeklyAvailability(SQLModel, table=True):
    __tablename__ = "weekly_availability"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="users.id", unique=True)
    created_at: dt.datetime = Field(
        default_factory=now_utc,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: dt.datetime = Field(
        default_factory=now_utc,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    # Relationship to DailyWindow
    windows: list["DailyWindow"] = Relationship(
        back_populates="weekly_availability",
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    @model_validator(mode="before")
    @classmethod
    def convert_datetimes_to_utc(cls, data):
        """Convert all datetime fields to UTC before validation."""
        if isinstance(data, dict):
            return convert_model_datetimes_to_utc(data)
        return data


class DailyWindow(SQLModel, table=True):
    __tablename__ = "daily_windows"
    __table_args__ = (
        UniqueConstraint(
            "weekly_availability_id",
            "day_of_week",
            "start_time",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    weekly_availability_id: int = Field(
        default=None, foreign_key="weekly_availability.id"
    )
    day_of_week: int = Field(default=0)
    start_time: dt.time = Field(sa_column=Column(Time))
    end_time: dt.time = Field(sa_column=Column(Time))

    # Relationship to WeeklyAvailability
    weekly_availability: WeeklyAvailability = Relationship(
        back_populates="windows", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @model_validator(mode="before")
    @classmethod
    def convert_datetimes_to_utc(cls, data):
        """Convert all datetime fields to UTC before validation."""
        if isinstance(data, dict):
            return convert_model_datetimes_to_utc(data)
        return data
