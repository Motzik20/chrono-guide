"""Utility functions for converting between scheduling models and schemas."""

from app.core.timezone import ensure_utc
from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.schemas.schedule_item import ScheduleItemCreate
from app.services.scheduling_types import (
    BusyInterval,
    SchedulableTask,
    ScheduleBlock,
)


def task_to_schedulable(task: Task) -> SchedulableTask:
    """
    Convert a Task model to a SchedulableTask for the scheduler.
    """
    if task.id is None:
        raise ValueError("Task must have an id to be schedulable")
    return SchedulableTask(
        id=task.id,
        title=task.title,
        description=task.description,
        expected_duration_minutes=task.expected_duration_minutes,
        deadline=ensure_utc(task.deadline),
        priority=task.priority,
    )


def tasks_to_schedulables(tasks: list[Task]) -> list[SchedulableTask]:
    """Convert a list of Task models to SchedulableTask models."""
    return [task_to_schedulable(task) for task in tasks]


def schedule_item_to_busy_interval(schedule_item: ScheduleItem) -> BusyInterval:
    """Convert a ScheduleItem to a BusyInterval for the scheduler."""
    start_time = ensure_utc(schedule_item.start_time)
    end_time = ensure_utc(schedule_item.end_time)
    if start_time is None or end_time is None:
        raise ValueError("Schedule item must have valid start_time and end_time")
    return BusyInterval(
        task_id=schedule_item.task_id,
        start_time=start_time,
        end_time=end_time,
        title=schedule_item.title,
    )


def schedule_items_to_busy_intervals(
    schedule_items: list[ScheduleItem],
) -> list[BusyInterval]:
    """Convert a list of ScheduleItems to BusyIntervals for the scheduler."""
    return [
        schedule_item_to_busy_interval(schedule_item)
        for schedule_item in schedule_items
    ]


def schedule_blocks_to_schedule_items(
    schedule_blocks: list[ScheduleBlock],
    user_id: int,
) -> list[ScheduleItemCreate]:
    """
    Convert schedule blocks to schedule item create schemas.

    This is a utility function that can be used by any scheduler implementation
    to convert their output format to database models.

    Args:
        schedule_blocks: List of schedule blocks from scheduling
        user_id: User ID for the schedule items

    Returns:
        List of schedule item create schemas
    """
    return [
        ScheduleItemCreate(
            user_id=user_id,
            task_id=schedule_block.task_id,
            start_time=schedule_block.start_time,
            end_time=schedule_block.end_time,
            source=schedule_block.source,
            title=schedule_block.title,
            description=schedule_block.description,
        )
        for schedule_block in schedule_blocks
    ]
