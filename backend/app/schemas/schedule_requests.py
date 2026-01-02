"""
Pydantic schemas for schedule-related API endpoints.
Only essential schemas - no duplication of existing models.
"""

from pydantic import BaseModel, Field

from app.services.scheduling_types import ScheduleBlock


class ScheduleGenerateRequest(BaseModel):
    """Request schema for generating a schedule."""

    task_ids: list[int] = Field(..., description="List of task IDs to schedule")
    preview: bool = Field(
        default=True, description="Whether to preview without committing"
    )


class ScheduleCommitRequest(BaseModel):
    """Request schema for committing a generated schedule."""

    schedule_blocks: list[ScheduleBlock] = Field(
        ..., description="Generated schedule blocks to commit"
    )


class ScheduleResponse(BaseModel):
    """Response schema for schedule operations."""

    schedule_blocks: list[ScheduleBlock] = Field(
        ..., description="Generated or committed schedule blocks"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Any warnings from scheduling"
    )
    total_duration_minutes: int = Field(
        ..., description="Total duration of scheduled tasks"
    )
