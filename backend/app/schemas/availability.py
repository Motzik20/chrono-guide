import datetime as dt
from collections.abc import Iterable
from enum import IntEnum
from typing import cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.availability import DailyWindowModel


class DayOfWeek(IntEnum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


class DailyWindow(BaseModel):
    start: dt.time
    end: dt.time


class WeeklyAvailabilityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # The DayOfWeek has a list of DailyWindows so you can have multiple working windows for the same day
    windows: dict[DayOfWeek, list[DailyWindow]] | None = Field(default_factory=lambda: {})

    @field_validator("windows", mode="before")
    @classmethod
    def convert_windows(cls, v: dict[DayOfWeek, list[DailyWindow]] | Iterable[DailyWindowModel] | None) -> dict[DayOfWeek, list[DailyWindow]]:
        """Convert SQLModel DailyWindow relationships to Pydantic format."""
        if v is None:
            return {}

        if isinstance(v, dict):
            return cast(dict[DayOfWeek, list[DailyWindow]], v)

        windows_dict: dict[DayOfWeek, list[DailyWindow]] = {}
        for window in v:
            day = DayOfWeek(window.day_of_week)
            if day not in windows_dict:
                windows_dict[day] = []

            windows_dict[day].append(
                DailyWindow(start=window.start_time, end=window.end_time)
            )
        return windows_dict


class WeeklyAvailabilityCreate(WeeklyAvailabilityBase):
    pass


class WeeklyAvailabilityUpdate(WeeklyAvailabilityBase):
    windows: dict[DayOfWeek, list[DailyWindow]] | None = None


class WeeklyAvailabilityRead(WeeklyAvailabilityBase):
    id: int
    user_id: int
    created_at: dt.datetime
    updated_at: dt.datetime
