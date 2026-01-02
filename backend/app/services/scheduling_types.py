"""Type definitions for the scheduling system."""

import datetime as dt
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.availability import WeeklyAvailabilityBase


class SchedulableTask(BaseModel):
    """A task that can be scheduled."""

    id: int
    title: str
    description: str | None = None
    expected_duration_minutes: int
    deadline: dt.datetime | None = None
    priority: int

    def can_fit_duration(self, duration_minutes: int) -> bool:
        """Check if this task can fit within the given duration."""
        return self.expected_duration_minutes <= duration_minutes


class BusyInterval(BaseModel):
    """A time interval that is already occupied."""

    task_id: int | None = None
    start_time: dt.datetime
    end_time: dt.datetime
    title: str | None = None


class ScheduleBlock(BaseModel):
    """A scheduled block of time for a task."""

    task_id: int
    start_time: dt.datetime
    end_time: dt.datetime
    source: str = "task"
    title: str | None = None
    description: str | None = None


class TimeSlot(BaseModel):
    """An available time slot for scheduling."""

    start: dt.datetime = Field(..., description="Start time of the slot")
    end: dt.datetime = Field(..., description="End time of the slot")

    @property
    def duration_minutes(self) -> float:
        """Duration of the slot in minutes."""
        return (self.end - self.start).total_seconds() / 60


class AvailableSlots(BaseModel):
    """Collection of available time slots."""

    slots: list[TimeSlot] = Field(default_factory=lambda: [])
    total_duration_minutes: int = Field(0)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.total_duration_minutes = int(
            sum(slot.duration_minutes for slot in self.slots)
        )

    def add_slots(self, slots: list[TimeSlot]) -> None:
        """Add slots to the collection."""
        self.slots.extend(slots)
        for slot in slots:
            self.total_duration_minutes += int(slot.duration_minutes)

    def merge_slots(self, other: "AvailableSlots") -> None:
        """Merge another AvailableSlots collection into this one."""
        self.slots.extend(other.slots)
        self.total_duration_minutes += other.total_duration_minutes


class SchedulerAvailability(WeeklyAvailabilityBase):
    """Availability schedule for the scheduler."""

    pass


class SchedulingConfig(BaseModel):
    """Configuration for the scheduling algorithm."""

    max_scheduling_weeks: int = 12
    allow_splitting: bool = True
    timezone: str = "UTC"


class SchedulingRequest(BaseModel):
    """Request to schedule tasks."""

    tasks: list[SchedulableTask]
    busy_intervals: list[BusyInterval]
    scheduler_availability: SchedulerAvailability
    config: SchedulingConfig
    start_time: dt.datetime


class SchedulingResponse(BaseModel):
    """Response from the scheduler with scheduled blocks and warnings."""

    schedule_blocks: list[ScheduleBlock]
    warnings: list[SchedulableTask] = Field(default_factory=lambda: [])
