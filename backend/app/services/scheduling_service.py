import datetime as dt
from collections import deque
from typing import Any

from pydantic import BaseModel, Field

from app.core.timezone import ensure_utc, get_next_half_hour, get_next_weekday, now_utc
from app.models.availability import WeeklyAvailability
from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.schemas.availability import DayOfWeek, WeeklyAvailabilityBase


class SchedulableTask(BaseModel):
    id: int
    title: str
    expected_duration_minutes: int
    deadline: dt.datetime | None = None
    priority: int

    def can_fit_duration(self, duration_minutes: int) -> bool:
        return self.expected_duration_minutes <= duration_minutes


class BusyInterval(BaseModel):
    task_id: int | None = None
    start_time: dt.datetime
    end_time: dt.datetime
    title: str | None = None


class ScheduleBlock(BaseModel):
    task_id: int
    start_time: dt.datetime
    end_time: dt.datetime
    source: str = "scheduler"
    title: str | None = None
    description: str | None = None
    reason: str | None = None


class TimeSlot(BaseModel):
    start: dt.datetime = Field(..., description="Start time of the slot")
    end: dt.datetime = Field(..., description="End time of the slot")

    @property
    def duration_minutes(self) -> float:
        """Duration of the slot in hours."""
        return (self.end - self.start).total_seconds() / 60


class AvailableSlots(BaseModel):
    """Collection of available time slots."""

    slots: list[TimeSlot] = Field(default_factory=lambda: [])
    total_duration_minutes: int = Field(0)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.total_duration_minutes = int(sum(slot.duration_minutes for slot in self.slots))

    def add_slots(self, slots: list[TimeSlot]) -> None:
        self.slots.extend(slots)
        for slot in slots:
            self.total_duration_minutes += int(slot.duration_minutes)

    def merge_slots(self, other: "AvailableSlots") -> None:
        self.slots.extend(other.slots)
        self.total_duration_minutes += other.total_duration_minutes


class SchedulerAvailability(WeeklyAvailabilityBase):
    pass


class SchedulingConfig(BaseModel):
    max_scheduling_weeks: int = 12
    min_block_minute: int = 30
    allow_splitting: bool = True


class SchedulingRequest(BaseModel):
    tasks: list[SchedulableTask]
    busy_intervals: list[BusyInterval]
    scheduler_availability: SchedulerAvailability
    config: SchedulingConfig
    start_time: dt.datetime


class SchedulingResponse(BaseModel):
    schedule_blocks: list[ScheduleBlock]
    warnings: list[SchedulableTask] = Field(
        default_factory=lambda: []
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
        expected_duration_minutes=task.expected_duration_minutes,
        deadline=ensure_utc(task.deadline),
        priority=task.priority,
    )


def tasks_to_schedulables(tasks: list[Task]) -> list[SchedulableTask]:
    return [task_to_schedulable(task) for task in tasks]


def schedule_item_to_busy_interval(schedule_item: ScheduleItem) -> BusyInterval:
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
    return [
        schedule_item_to_busy_interval(schedule_item)
        for schedule_item in schedule_items
    ]


def schedule_tasks(
    tasks: list[Task],
    schedule_items: list[ScheduleItem],
    availability: WeeklyAvailability,
) -> SchedulingResponse:
    """
    Pure scheduling function that takes pre-fetched data and returns schedule blocks.

    Args:
        tasks: List of tasks to schedule
        busy_intervals: List of busy time intervals
        availability: User's weekly availability
        config: Scheduling configuration (defaults to SchedulingConfig())

    Returns:
        SchedulingResponse with schedule blocks and warnings as unscheduled tasks
    """
    if not tasks:
        return SchedulingResponse(
            schedule_blocks=[],
            warnings=[],
        )

    schedulable_tasks = tasks_to_schedulables(tasks)
    busy_intervals = schedule_items_to_busy_intervals(schedule_items)
    scheduler_availability = SchedulerAvailability.model_validate(availability)
    start_time = get_next_half_hour(now_utc())

    request = SchedulingRequest(
        tasks=schedulable_tasks,
        busy_intervals=busy_intervals,
        scheduler_availability=scheduler_availability,
        config=SchedulingConfig(),
        start_time=start_time,
    )

    return schedule(request)


def schedule(
    request: SchedulingRequest,
) -> SchedulingResponse:
    """
    Schedules the tasks in the request.
    """
    ranked_tasks: list[SchedulableTask] = rank_tasks(request.tasks, request.start_time)
    schedule_blocks: list[ScheduleBlock] = []
    week_end = get_next_weekday(request.start_time, weekday=DayOfWeek.MON)
    week_busy = [
        bi
        for bi in request.busy_intervals
        if request.start_time <= bi.start_time < week_end
    ]
    available_slots: AvailableSlots = get_available_time_slots(
        week_busy, request.scheduler_availability, request.start_time
    )
    for _ in range(1, request.config.max_scheduling_weeks):
        week_start = week_end
        week_end = week_end + dt.timedelta(days=7)
        week_busy = [
            bi
            for bi in request.busy_intervals
            if week_start <= bi.start_time < week_end
        ]
        week_slots = get_available_time_slots(
            week_busy, request.scheduler_availability, week_start
        )
        available_slots.merge_slots(week_slots)

    schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
        ranked_tasks, available_slots, request.config.allow_splitting
    )

    return SchedulingResponse(
        schedule_blocks=schedule_blocks, warnings=unscheduled_tasks
    )


def get_available_time_slots(
    busy_intervals: list[BusyInterval],
    availability: SchedulerAvailability,
    week_start: dt.datetime,
) -> AvailableSlots:
    available_slots: AvailableSlots = AvailableSlots()
    start_weekday_int: int = week_start.date().weekday()
    start_weekday: DayOfWeek = DayOfWeek(start_weekday_int)
    for day_offset in range(start_weekday_int, 7):
        current_date: dt.date = week_start.date() + dt.timedelta(
            days=day_offset - start_weekday_int
        )
        day_of_week_int: int = current_date.weekday()
        day_of_week: DayOfWeek = DayOfWeek(day_of_week_int)

        if availability.windows is None or day_of_week not in availability.windows.keys():
            continue

        day_windows = availability.windows[day_of_week]

        for window in day_windows:
            window_start_raw = ensure_utc(
                dt.datetime.combine(current_date, window.start)
            )
            window_end_raw = ensure_utc(
                dt.datetime.combine(current_date, window.end)
            )
            if window_start_raw is None or window_end_raw is None:
                continue
            window_start: dt.datetime = window_start_raw
            window_end: dt.datetime = window_end_raw

            if start_weekday == day_offset:
                if window_end <= week_start:
                    continue
                elif window_start < week_start:
                    window_start = week_start

            overlapping_busy: list[BusyInterval] = [
                bi
                for bi in busy_intervals
                if (bi.start_time < window_end and bi.end_time > window_start)
            ]

            free_slots = subtract_busy_from_window(
                window_start, window_end, overlapping_busy
            )

            available_slots.add_slots(free_slots)

    return available_slots


def subtract_busy_from_window(
    window_start: dt.datetime,
    window_end: dt.datetime,
    overlapping_busy: list[BusyInterval],
) -> list[TimeSlot]:
    if not overlapping_busy:
        return [TimeSlot(start=window_start, end=window_end)]

    sorted_busy = sorted(overlapping_busy, key=lambda bi: bi.start_time)
    current_start = window_start
    free_slots: list[TimeSlot] = []
    for busy in sorted_busy:
        # if the busy starts somewhere inside the window, there is a free gap
        if busy.start_time > current_start:
            new_slot = TimeSlot(
                start=current_start, end=min(busy.start_time, window_end)
            )
            free_slots.append(new_slot)
        current_start = max(
            current_start, busy.end_time
        )  # edge case where nested busy intervals are happening

    if current_start < window_end:
        new_slot = TimeSlot(start=current_start, end=window_end)
        free_slots.append(new_slot)

    return free_slots


def rank_tasks(tasks: list[SchedulableTask], now: dt.datetime) -> list[SchedulableTask]:
    """
    Ranks the tasks in the request according to these hierarchy rules:
    1. Tasks with a deadline are ranked higher
    2. Tasks with a higher priority are ranked higher but below tasks with a deadline
    3. Tasks with a longer expected duration are ranked higher but below tasks with a higher priority
    """

    def get_sort_key(task: SchedulableTask) -> tuple[int, int, int]:
        if task.deadline:
            deadline_rank = int((task.deadline - now).total_seconds() / 60)
        else:
            deadline_rank = 999999999

        return (deadline_rank, task.priority, -task.expected_duration_minutes)

    return sorted(tasks, key=get_sort_key)


def place_tasks_in_slots(
    tasks: list[SchedulableTask],
    free_slots: AvailableSlots,
    split_tasks: bool,
) -> tuple[list[ScheduleBlock], list[SchedulableTask]]:
    """
    Place tasks into available time slots.

    Returns:
        tuple: (scheduled_blocks, unscheduled_tasks)
    """
    schedule_blocks: list[ScheduleBlock] = []
    remaining_tasks: deque[SchedulableTask] = deque(tasks.copy())

    for slot in free_slots.slots:
        schedule_blocks.extend(_fill_single_slot(slot, remaining_tasks, split_tasks))

    unscheduled_tasks: list[SchedulableTask] = list(remaining_tasks)
    return schedule_blocks, unscheduled_tasks


def _create_schedule_block(
    task: SchedulableTask, start_time: dt.datetime
) -> ScheduleBlock:
    end_time = start_time + dt.timedelta(minutes=task.expected_duration_minutes)
    return ScheduleBlock(
        task_id=task.id,
        start_time=start_time,
        end_time=end_time,
        source="scheduler",
        title=task.title,
        description=f"Scheduled task: {task.title}",
        reason=task.title,
    )


def _fill_single_slot(
    slot: TimeSlot,
    remaining_tasks: deque[SchedulableTask],
    split_tasks: bool,
) -> list[ScheduleBlock]:
    slot_position = slot.start
    remaining_slot_duration = int(slot.duration_minutes)
    schedule_blocks: list[ScheduleBlock] = []
    while remaining_slot_duration > 0 and remaining_tasks:
        task = remaining_tasks.popleft()

        if not task.can_fit_duration(remaining_slot_duration):
            if split_tasks:
                remainder_duration = (
                    task.expected_duration_minutes - remaining_slot_duration
                )
                task_split = task.model_copy()
                task_split.expected_duration_minutes = remainder_duration

                task.expected_duration_minutes = remaining_slot_duration

                remaining_tasks.appendleft(task_split)
            else:
                fitting_task = _find_best_fitting_task(
                    remaining_tasks, remaining_slot_duration
                )
                if fitting_task:
                    _remove_task_from_deque(remaining_tasks, fitting_task)
                    remaining_tasks.appendleft(task)
                    task = fitting_task
                else:
                    remaining_tasks.appendleft(task)
                    break

        schedule_block = _create_schedule_block(task, slot_position)

        slot_position = schedule_block.end_time
        remaining_slot_duration -= task.expected_duration_minutes
        schedule_blocks.append(schedule_block)

    return schedule_blocks


def _find_best_fitting_task(
    tasks: deque[SchedulableTask], max_duration: int
) -> SchedulableTask | None:
    return next(
        (task for task in tasks if task.can_fit_duration(max_duration)),
        None,
    )


def _remove_task_from_deque(
    tasks: deque[SchedulableTask],
    task: SchedulableTask,
) -> None:
    temp_queue: deque[SchedulableTask] = deque()
    found = False
    while tasks and not found:
        candidate = tasks.popleft()
        if candidate.id == task.id:
            found = True
        else:
            temp_queue.append(candidate)
    tasks.extendleft(reversed(temp_queue))
