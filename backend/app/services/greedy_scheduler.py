"""Greedy scheduling algorithm implementation."""

import datetime as dt
from collections import deque

from app.core.timezone import (
    get_next_half_hour,
    get_next_weekday,
    now_utc,
    parse_user_datetime,
)
from app.models.availability import WeeklyAvailability
from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.schemas.availability import DayOfWeek
from app.services.scheduling_types import (
    AvailableSlots,
    BusyInterval,
    SchedulableTask,
    ScheduleBlock,
    SchedulerAvailability,
    SchedulingConfig,
    SchedulingRequest,
    SchedulingResponse,
    TimeSlot,
)


class GreedyScheduler:
    """
    Greedy scheduling algorithm implementation of ChronoScheduler protocol.

    This scheduler uses a greedy approach to fill available time slots with tasks,
    prioritizing tasks with deadlines, then by priority, then by duration.
    """

    def schedule_tasks(
        self,
        tasks: list[Task],
        schedule_items: list[ScheduleItem],
        availability: WeeklyAvailability,
        config: SchedulingConfig,
    ) -> SchedulingResponse:
        """
        Schedule tasks into available time slots.

        Args:
            tasks: List of tasks to schedule
            schedule_items: Existing schedule items (busy intervals)
            availability: User's weekly availability
            config: Scheduling configuration

        Returns:
            SchedulingResponse with schedule blocks and warnings as unscheduled tasks
        """
        if not tasks:
            return SchedulingResponse(
                schedule_blocks=[],
                warnings=[],
            )

        from app.services.scheduling_utils import (
            schedule_items_to_busy_intervals,
            tasks_to_schedulables,
        )

        schedulable_tasks = tasks_to_schedulables(tasks)
        busy_intervals = schedule_items_to_busy_intervals(schedule_items)
        scheduler_availability = SchedulerAvailability.model_validate(availability)
        start_time = get_next_half_hour(now_utc())

        request = SchedulingRequest(
            tasks=schedulable_tasks,
            busy_intervals=busy_intervals,
            scheduler_availability=scheduler_availability,
            config=config,
            start_time=start_time,
        )

        return self._schedule(request)

    def _schedule(self, request: SchedulingRequest) -> SchedulingResponse:
        """
        Internal method: Schedules the tasks in the request.
        """
        ranked_tasks: list[SchedulableTask] = self._rank_tasks(
            request.tasks, request.start_time
        )
        schedule_blocks: list[ScheduleBlock] = []
        week_end = get_next_weekday(request.start_time, weekday=DayOfWeek.MON)
        week_busy = [
            bi
            for bi in request.busy_intervals
            if request.start_time <= bi.start_time < week_end
        ]
        available_slots: AvailableSlots = self._get_available_time_slots(
            week_busy,
            request.scheduler_availability,
            request.start_time,
            request.config.timezone,
        )
        for _ in range(1, request.config.max_scheduling_weeks):
            week_start = week_end
            week_end = week_end + dt.timedelta(days=7)
            week_busy = [
                bi
                for bi in request.busy_intervals
                if week_start <= bi.start_time < week_end
            ]
            week_slots = self._get_available_time_slots(
                week_busy,
                request.scheduler_availability,
                week_start,
                request.config.timezone,
            )
            available_slots.merge_slots(week_slots)

        schedule_blocks, unscheduled_tasks = self._place_tasks_in_slots(
            ranked_tasks, available_slots, request.config.allow_splitting
        )

        return SchedulingResponse(
            schedule_blocks=schedule_blocks, warnings=unscheduled_tasks
        )

    def _get_available_time_slots(
        self,
        busy_intervals: list[BusyInterval],
        availability: SchedulerAvailability,
        week_start: dt.datetime,
        user_timezone: str,
    ) -> AvailableSlots:
        """Internal method: Get available time slots for a week."""
        available_slots: AvailableSlots = AvailableSlots()
        start_weekday_int: int = week_start.date().weekday()
        start_weekday: DayOfWeek = DayOfWeek(start_weekday_int)
        for day_offset in range(start_weekday_int, 7):
            current_date: dt.date = week_start.date() + dt.timedelta(
                days=day_offset - start_weekday_int
            )
            day_of_week_int: int = current_date.weekday()
            day_of_week: DayOfWeek = DayOfWeek(day_of_week_int)

            if day_of_week not in availability.windows.keys():
                continue

            day_windows = availability.windows[day_of_week]

            for window in day_windows:
                window_start_raw = parse_user_datetime(
                    dt.datetime.combine(current_date, window.start), user_timezone
                )
                window_end_raw = parse_user_datetime(
                    dt.datetime.combine(current_date, window.end), user_timezone
                )
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

                free_slots = self._subtract_busy_from_window(
                    window_start, window_end, overlapping_busy
                )

                available_slots.add_slots(free_slots)

        return available_slots

    def _subtract_busy_from_window(
        self,
        window_start: dt.datetime,
        window_end: dt.datetime,
        overlapping_busy: list[BusyInterval],
    ) -> list[TimeSlot]:
        """Internal method: Calculate free slots by subtracting busy intervals."""
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

    def _rank_tasks(
        self, tasks: list[SchedulableTask], now: dt.datetime
    ) -> list[SchedulableTask]:
        """
        Internal method: Ranks the tasks according to these hierarchy rules:
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

    def _place_tasks_in_slots(
        self,
        tasks: list[SchedulableTask],
        free_slots: AvailableSlots,
        split_tasks: bool,
    ) -> tuple[list[ScheduleBlock], list[SchedulableTask]]:
        """
        Internal method: Place tasks into available time slots.

        Returns:
            tuple: (scheduled_blocks, unscheduled_tasks)
        """
        schedule_blocks: list[ScheduleBlock] = []
        remaining_tasks: deque[SchedulableTask] = deque(tasks.copy())

        for slot in free_slots.slots:
            schedule_blocks.extend(
                self._fill_single_slot(slot, remaining_tasks, split_tasks)
            )

        unscheduled_tasks: list[SchedulableTask] = list(remaining_tasks)
        return schedule_blocks, unscheduled_tasks

    def _create_schedule_block(
        self, task: SchedulableTask, start_time: dt.datetime
    ) -> ScheduleBlock:
        """Internal method: Create a schedule block from a task."""
        end_time = start_time + dt.timedelta(minutes=task.expected_duration_minutes)
        return ScheduleBlock(
            task_id=task.id,
            start_time=start_time,
            end_time=end_time,
            source="task",
            title=task.title,
            description=task.description,
        )

    def _fill_single_slot(
        self,
        slot: TimeSlot,
        remaining_tasks: deque[SchedulableTask],
        split_tasks: bool,
    ) -> list[ScheduleBlock]:
        """Internal method: Fill a single time slot with tasks."""
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
                    fitting_task = self._find_best_fitting_task(
                        remaining_tasks, remaining_slot_duration
                    )
                    if fitting_task:
                        self._remove_task_from_deque(remaining_tasks, fitting_task)
                        remaining_tasks.appendleft(task)
                        task = fitting_task
                    else:
                        remaining_tasks.appendleft(task)
                        break

            schedule_block = self._create_schedule_block(task, slot_position)

            slot_position = schedule_block.end_time
            remaining_slot_duration -= task.expected_duration_minutes
            schedule_blocks.append(schedule_block)

        return schedule_blocks

    def _find_best_fitting_task(
        self, tasks: deque[SchedulableTask], max_duration: int
    ) -> SchedulableTask | None:
        """Internal method: Find the best task that fits in the given duration."""
        return next(
            (task for task in tasks if task.can_fit_duration(max_duration)),
            None,
        )

    def _remove_task_from_deque(
        self, tasks: deque[SchedulableTask], task: SchedulableTask
    ) -> None:
        """Internal method: Remove a specific task from a deque."""
        temp_queue: deque[SchedulableTask] = deque()
        found = False
        while tasks and not found:
            candidate = tasks.popleft()
            if candidate.id == task.id:
                found = True
            else:
                temp_queue.append(candidate)
        tasks.extendleft(reversed(temp_queue))


# Keep the function for backward compatibility (can be removed later if not used)
def schedule_tasks(
    tasks: list[Task],
    schedule_items: list[ScheduleItem],
    availability: WeeklyAvailability,
    config: SchedulingConfig,
) -> SchedulingResponse:
    """
    Pure scheduling function that takes pre-fetched data and returns schedule blocks.

    DEPRECATED: Use GreedyScheduler().schedule_tasks() instead.

    Args:
        tasks: List of tasks to schedule
        busy_intervals: List of busy time intervals
        availability: User's weekly availability
        config: Scheduling configuration (defaults to SchedulingConfig())

    Returns:
        SchedulingResponse with schedule blocks and warnings as unscheduled tasks
    """
    scheduler = GreedyScheduler()
    return scheduler.schedule_tasks(tasks, schedule_items, availability, config)
