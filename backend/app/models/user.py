import datetime as dt

from pydantic import model_validator
from sqlalchemy import func
from sqlmodel import Column, DateTime, Field, SQLModel

from app.core.timezone import convert_model_datetimes_to_utc, now_utc


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    password: str = Field()
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
