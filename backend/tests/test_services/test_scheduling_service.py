import copy
import datetime as dt
import random
from collections import deque

from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.timezone import ensure_utc, get_next_weekday, now_utc
from app.models.availability import WeeklyAvailability
from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.models.user import User
from app.schemas.availability import DailyWindow as DailyWindowSchema
from app.schemas.availability import DayOfWeek
from app.services.scheduling_service import (  # noqa: PLC2701
    AvailableSlots,
    BusyInterval,
    SchedulableTask,
    ScheduleBlock,
    SchedulerAvailability,
    SchedulingConfig,
    SchedulingRequest,
    SchedulingResponse,
    TimeSlot,
    _create_schedule_block,  # type: ignore[attr-defined]
    _fill_single_slot,  # type: ignore[attr-defined]
    _find_best_fitting_task,  # type: ignore[attr-defined]
    _remove_task_from_deque,  # type: ignore[attr-defined]
    get_available_time_slots,
    place_tasks_in_slots,
    rank_tasks,
    schedule,
    schedule_items_to_busy_intervals,
    schedule_tasks,
    subtract_busy_from_window,
    task_to_schedulable,
    tasks_to_schedulables,
)
from tests.conftest import (
    available_slots_strategy,
    busy_intervals_strategy,
    schedulable_task_strategy,
    weekly_availability_strategy,
)


def get_remaining_free_slots(
    original_slots: AvailableSlots, schedule_blocks: list[ScheduleBlock]
) -> AvailableSlots:
    """
    Test utility: Calculate which parts of the original available slots are still free
    after placing the scheduled blocks.

    Returns:
        AvailableSlots: The remaining free time slots
    """
    if not schedule_blocks:
        return original_slots

    sorted_blocks = sorted(schedule_blocks, key=lambda sb: sb.start_time)

    remaining_slots: list[TimeSlot] = []

    for original_slot in original_slots.slots:
        overlapping_blocks = [
            block
            for block in sorted_blocks
            if block.start_time < original_slot.end
            and block.end_time > original_slot.start
        ]

        if not overlapping_blocks:
            remaining_slots.append(original_slot)
            continue

        current_pos = original_slot.start

        for block in overlapping_blocks:
            if current_pos < block.start_time:
                free_slot = TimeSlot(start=current_pos, end=block.start_time)
                remaining_slots.append(free_slot)

            current_pos = max(current_pos, block.end_time)

        if current_pos < original_slot.end:
            free_slot = TimeSlot(start=current_pos, end=original_slot.end)
            remaining_slots.append(free_slot)

    return AvailableSlots(slots=remaining_slots)


class TestSchedulingConversions:
    def test_task_conversion(self, task: Task) -> None:
        schedulable: SchedulableTask = task_to_schedulable(task)
        assert schedulable.title is not None
        assert schedulable.id == task.id  # type: ignore[attr-defined]
        assert schedulable.title == task.title

    def test_tasks_conversion(self, task_list: list[Task]) -> None:
        schedulables: list[SchedulableTask] = tasks_to_schedulables(task_list)
        for index, schedulable in enumerate(schedulables):
            task: Task = task_list[index]
            manual_schedulable: SchedulableTask = task_to_schedulable(task)
            assert schedulable == manual_schedulable
            assert schedulable.id == task.id  # type: ignore[attr-defined]
            assert schedulable.title == task.title
            assert schedulable.deadline == ensure_utc(task.deadline)


class TestSchedulingRanking:
    def test_rank_tasks(
        self,
        task_list: list[Task],
        task: Task,
        urgent_task: Task,
        longer_task: Task,
        deadline_task: Task,
        later_deadline_task: Task,
        urgent_later_deadline_task: Task,
    ) -> None:
        now: dt.datetime = now_utc()
        schedulables: list[SchedulableTask] = tasks_to_schedulables(task_list)
        ranked_schedulables: list[SchedulableTask] = rank_tasks(schedulables, now)
        manually_ranked_tasks: list[Task] = [
            deadline_task,
            urgent_later_deadline_task,
            later_deadline_task,
            urgent_task,
            longer_task,
            task,
        ]

        manually_ranked_schedulables: list[SchedulableTask] = tasks_to_schedulables(
            manually_ranked_tasks
        )

        assert ranked_schedulables == manually_ranked_schedulables

    @settings(max_examples=1000)
    @given(st.lists(schedulable_task_strategy(), min_size=1, max_size=1000))
    def test_rank_tasks_stratgey(self, task_list: list[SchedulableTask]) -> None:
        unique_tasks = {task.id: task for task in task_list}
        task_list = list(unique_tasks.values())

        now: dt.datetime = now_utc()
        ranked_schedulables: list[SchedulableTask] = rank_tasks(task_list, now)
        for i, ranked_schedulable in enumerate(ranked_schedulables[:-1]):
            next_schedulable = ranked_schedulables[(i + 1) % len(ranked_schedulables)]
            if ranked_schedulable.deadline is None:
                assert next_schedulable.deadline is None
                assert ranked_schedulable.priority <= next_schedulable.priority
                if ranked_schedulable.priority == next_schedulable.priority:
                    assert (
                        ranked_schedulable.expected_duration_minutes
                        >= next_schedulable.expected_duration_minutes
                    )
            elif next_schedulable.deadline is None:
                assert ranked_schedulable.deadline is not None
            else:
                assert ranked_schedulable.deadline <= next_schedulable.deadline
                if ranked_schedulable.deadline == next_schedulable.deadline:
                    assert ranked_schedulable.priority <= next_schedulable.priority
                    if ranked_schedulable.priority == next_schedulable.priority:
                        assert (
                            ranked_schedulable.expected_duration_minutes
                            >= next_schedulable.expected_duration_minutes
                        )

    def test_rank_tasks_same_deadline_different_priority(self) -> None:
        now = dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc)
        same_deadline = now + dt.timedelta(hours=4)

        tasks = [
            SchedulableTask(
                id=1,
                title="Low priority",
                expected_duration_minutes=60,
                priority=3,
                deadline=same_deadline,
            ),
            SchedulableTask(
                id=2,
                title="High priority",
                expected_duration_minutes=60,
                priority=0,
                deadline=same_deadline,
            ),
        ]

        ranked = rank_tasks(tasks, now)

        # Higher priority should come first
        assert ranked[0].id == 2
        assert ranked[1].id == 1

    def test_rank_tasks_same_priority_different_duration(self) -> None:
        now = dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc)

        tasks = [
            SchedulableTask(
                id=1, title="Short task", expected_duration_minutes=30, priority=2
            ),
            SchedulableTask(
                id=2, title="Long task", expected_duration_minutes=120, priority=2
            ),
        ]

        ranked = rank_tasks(tasks, now)

        # Longer duration should come first (negative duration in sort key)
        assert ranked[0].id == 2
        assert ranked[1].id == 1

    def test_rank_tasks_deadline_priority(self) -> None:
        now = dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc)

        tasks = [
            SchedulableTask(
                id=1,
                title="No deadline, low priority",
                expected_duration_minutes=60,
                priority=3,
            ),
            SchedulableTask(
                id=2,
                title="Far deadline, high priority",
                expected_duration_minutes=60,
                priority=0,
                deadline=now + dt.timedelta(days=7),
            ),
            SchedulableTask(
                id=3,
                title="Near deadline, low priority",
                expected_duration_minutes=60,
                priority=3,
                deadline=now + dt.timedelta(hours=2),
            ),
            SchedulableTask(
                id=4,
                title="No deadline, high priority",
                expected_duration_minutes=60,
                priority=0,
            ),
        ]

        ranked = rank_tasks(tasks, now)

        # Should be ranked by: deadline (near first), then priority, then duration
        assert ranked[0].id == 3  # Near deadline
        assert ranked[1].id == 2  # Far deadline
        assert ranked[2].id == 4  # No deadline, high priority
        assert ranked[3].id == 1  # No deadline, low priority


class TestSubtractingBusyFromWindow:
    def test_simple_subtract_busy_from_window(
        self,
        daily_window_start: dt.datetime,
        daily_window_end: dt.datetime,
        busy_interval: BusyInterval,
    ) -> None:
        end_first_window: dt.datetime = daily_window_start + dt.timedelta(hours=2)
        start_second_window: dt.datetime = daily_window_start + dt.timedelta(hours=4)
        free_slots: list[TimeSlot] = subtract_busy_from_window(
            daily_window_start, daily_window_end, [busy_interval]
        )
        first_slot = TimeSlot(start=daily_window_start, end=end_first_window)
        second_slot = TimeSlot(start=start_second_window, end=daily_window_end)
        assert free_slots[0].start == first_slot.start
        assert free_slots[0].end == first_slot.end
        assert free_slots[1].start == second_slot.start
        assert free_slots[1].end == second_slot.end

    def test_complex_subtract_busy_from_window(
        self,
        daily_window_start: dt.datetime,
        daily_window_end: dt.datetime,
        busy_interval: BusyInterval,
    ) -> None:
        nested_busy_interval: BusyInterval = copy.deepcopy(busy_interval)
        nested_busy_interval.start_time = busy_interval.start_time + dt.timedelta(
            minutes=30
        )
        nested_busy_interval.end_time = busy_interval.end_time - dt.timedelta(
            minutes=30
        )

        later_busy_interval: BusyInterval = copy.deepcopy(busy_interval)
        later_busy_interval.start_time = busy_interval.start_time + dt.timedelta(
            hours=3
        )
        later_busy_interval.end_time = busy_interval.end_time + dt.timedelta(hours=3)
        busy_intervals = [later_busy_interval, nested_busy_interval, busy_interval]
        free_slots = subtract_busy_from_window(
            daily_window_start, daily_window_end, busy_intervals
        )
        assert free_slots

    def test_empty_subtract_busy_from_window(
        self, daily_window_start: dt.datetime, daily_window_end: dt.datetime
    ) -> None:
        free_slots = subtract_busy_from_window(daily_window_start, daily_window_end, [])
        assert free_slots[0].start == daily_window_start
        assert free_slots[0].end == daily_window_end

    @settings(max_examples=10000)
    @given(
        st.integers(min_value=0, max_value=22),
        st.integers(min_value=1, max_value=23),
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=22),
                st.integers(min_value=1, max_value=23),
            ),
            min_size=0,
            max_size=5,
        ),
    )
    def test_random_subtract_busy_from_window(
        self, start_hour: int, end_hour: int, busy_hours: list[tuple[int, int]]
    ):
        """Property-based test that generates random test cases for subtract_busy_from_window."""
        if end_hour <= start_hour:
            end_hour = start_hour + 1

        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
        window_start = tomorrow.replace(
            hour=start_hour, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
        )
        window_end = tomorrow.replace(
            hour=end_hour, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
        )

        busy_intervals: list[BusyInterval] = []
        for busy_start_hour, busy_end_hour in busy_hours:
            if busy_end_hour <= busy_start_hour:
                continue

            if busy_start_hour < end_hour and busy_end_hour > start_hour:
                busy_start = tomorrow.replace(
                    hour=busy_start_hour,
                    minute=0,
                    second=0,
                    microsecond=0,
                    tzinfo=dt.timezone.utc,
                )
                busy_end = tomorrow.replace(
                    hour=busy_end_hour,
                    minute=0,
                    second=0,
                    microsecond=0,
                    tzinfo=dt.timezone.utc,
                )

                if busy_start < busy_end:
                    busy_intervals.append(
                        BusyInterval(
                            task_id=1,
                            start_time=busy_start,
                            end_time=busy_end,
                            title="Random busy interval",
                        )
                    )

        if not busy_intervals:
            free_slots = subtract_busy_from_window(window_start, window_end, [])
            assert len(free_slots) == 1
            assert free_slots[0].start == window_start
            assert free_slots[0].end == window_end
            return

        assert len(busy_intervals) > 0, (
            "Should have overlapping busy intervals for main test logic"
        )

        free_slots = subtract_busy_from_window(window_start, window_end, busy_intervals)

        # Property 1: All free slots should be within the window
        for free_slot in free_slots:
            assert free_slot.start >= window_start, (
                f"Free slot starts before window: {free_slot.start} < {window_start}"
            )
            assert free_slot.end <= window_end, (
                f"Free slot ends after window: {free_slot.end} > {window_end}"
            )
            assert free_slot.start < free_slot.end, (
                f"Invalid slot: {free_slot.start} >= {free_slot.end}"
            )

        # Property 2: Free slots should not overlap with busy intervals
        for free_slot in free_slots:
            for busy in busy_intervals:
                overlap = (
                    free_slot.start < busy.end_time and free_slot.end > busy.start_time
                )
                assert not overlap, (
                    f"Free slot overlaps with busy interval: {free_slot.start}-{free_slot.end} vs {busy.start_time}-{busy.end_time}"
                )

        # Property 3: Free slots should not overlap with each other
        for i, slot1 in enumerate(free_slots):
            for j, slot2 in enumerate(free_slots):
                if i != j:
                    overlap = slot1.start < slot2.end and slot1.end > slot2.start
                    assert not overlap, (
                        f"Free slots overlap: {slot1.start}-{slot1.end} vs {slot2.start}-{slot2.end}"
                    )

        # Property 4: The total time covered by free slots should equal the window minus the actual covered busy time
        total_free_time = sum(
            slot.duration_minutes * 60
            for slot in free_slots  # Convert to seconds
        )

        sorted_busy = sorted(busy_intervals, key=lambda bi: bi.start_time)
        merged_intervals: list[tuple[dt.datetime, dt.datetime]] = []
        current_start = sorted_busy[0].start_time
        current_end = sorted_busy[0].end_time

        for busy in sorted_busy[1:]:
            if busy.start_time <= current_end:
                current_end = max(current_end, busy.end_time)
            else:
                merged_intervals.append((current_start, current_end))
                current_start = busy.start_time
                current_end = busy.end_time

        merged_intervals.append((current_start, current_end))

        covered_busy_time = 0
        for start, end in merged_intervals:
            overlap_start = max(start, window_start)
            overlap_end = min(end, window_end)
            if overlap_start < overlap_end:
                covered_busy_time += (overlap_end - overlap_start).total_seconds()

        window_time = (window_end - window_start).total_seconds()

        assert abs(total_free_time + covered_busy_time - window_time) < 1.0, (
            f"Time mismatch: free={total_free_time}s, covered_busy={covered_busy_time}s, "
            f"window={window_time}s, diff={abs(total_free_time + covered_busy_time - window_time)}s"
        )

        for i in range(len(free_slots) - 1):
            assert free_slots[i].end <= free_slots[i + 1].start, (
                f"Free slots not in order: {free_slots[i]} followed by {free_slots[i + 1]}"
            )

    def test_subtract_busy_single_overlap(self):
        """Test subtracting a single busy interval that overlaps with window."""
        window_start = dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
        window_end = dt.datetime(2024, 1, 1, 17, 0, tzinfo=dt.timezone.utc)

        busy_intervals = [
            BusyInterval(
                task_id=1,
                start_time=dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc),
                end_time=dt.datetime(2024, 1, 1, 14, 0, tzinfo=dt.timezone.utc),
                title="Lunch",
            )
        ]

        free_slots = subtract_busy_from_window(window_start, window_end, busy_intervals)

        assert len(free_slots) == 2
        assert free_slots[0].start == window_start
        assert free_slots[0].end == busy_intervals[0].start_time
        assert free_slots[1].start == busy_intervals[0].end_time
        assert free_slots[1].end == window_end

    def test_subtract_busy_multiple_overlaps(self):
        """Test subtracting multiple overlapping busy intervals."""
        window_start = dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
        window_end = dt.datetime(2024, 1, 1, 17, 0, tzinfo=dt.timezone.utc)

        busy_intervals = [
            BusyInterval(
                task_id=1,
                start_time=dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc),
                end_time=dt.datetime(2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc),
                title="Meeting 1",
            ),
            BusyInterval(
                task_id=2,
                start_time=dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc),
                end_time=dt.datetime(2024, 1, 1, 13, 0, tzinfo=dt.timezone.utc),
                title="Meeting 2",
            ),
            BusyInterval(
                task_id=3,
                start_time=dt.datetime(2024, 1, 1, 15, 0, tzinfo=dt.timezone.utc),
                end_time=dt.datetime(2024, 1, 1, 16, 0, tzinfo=dt.timezone.utc),
                title="Meeting 3",
            ),
        ]

        free_slots = subtract_busy_from_window(window_start, window_end, busy_intervals)

        assert len(free_slots) == 4
        # Check that free slots are in correct order and don't overlap with busy intervals
        for i, slot in enumerate(free_slots):
            assert slot.start < slot.end
            if i > 0:
                assert free_slots[i - 1].end <= slot.start

    def test_subtract_busy_nested_intervals(self):
        """Test subtracting nested busy intervals (one inside another)."""
        window_start = dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
        window_end = dt.datetime(2024, 1, 1, 17, 0, tzinfo=dt.timezone.utc)

        busy_intervals = [
            BusyInterval(
                task_id=1,
                start_time=dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc),
                end_time=dt.datetime(2024, 1, 1, 14, 0, tzinfo=dt.timezone.utc),
                title="Long meeting",
            ),
            BusyInterval(
                task_id=2,
                start_time=dt.datetime(2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc),
                end_time=dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc),
                title="Nested meeting",
            ),
        ]

        free_slots = subtract_busy_from_window(window_start, window_end, busy_intervals)

        assert len(free_slots) == 2
        assert free_slots[0].start == window_start
        assert free_slots[0].end == busy_intervals[0].start_time
        assert free_slots[1].start == busy_intervals[0].end_time
        assert free_slots[1].end == window_end

    def test_subtract_busy_no_overlap(self):
        """Test subtracting busy intervals that don't overlap with window."""
        window_start = dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
        window_end = dt.datetime(2024, 1, 1, 17, 0, tzinfo=dt.timezone.utc)

        busy_intervals = [
            BusyInterval(
                task_id=1,
                start_time=dt.datetime(
                    2024, 1, 1, 18, 0, tzinfo=dt.timezone.utc
                ),  # After window
                end_time=dt.datetime(2024, 1, 1, 19, 0, tzinfo=dt.timezone.utc),
                title="After hours",
            ),
            BusyInterval(
                task_id=2,
                start_time=dt.datetime(
                    2024, 1, 1, 7, 0, tzinfo=dt.timezone.utc
                ),  # Before window
                end_time=dt.datetime(2024, 1, 1, 8, 0, tzinfo=dt.timezone.utc),
                title="Early morning",
            ),
        ]

        free_slots = subtract_busy_from_window(window_start, window_end, busy_intervals)

        assert len(free_slots) == 1
        assert free_slots[0].start == window_start
        assert free_slots[0].end == window_end


class TestAvailableTimeSlots:
    @given(
        weekly_availability_strategy(),
        busy_intervals_strategy(min_date=get_next_weekday(now_utc())),
    )
    def test_available_time_slots(
        self,
        st_weekly_availability: SchedulerAvailability,
        busy_intervals: list[BusyInterval],
    ):
        next_monday = get_next_weekday(now_utc())
        available_slots: AvailableSlots = get_available_time_slots(
            busy_intervals, st_weekly_availability, next_monday, "UTC"
        )
        assert st_weekly_availability.windows is not None
        if not busy_intervals:
            index: int = 0
            daily_windows_duration: float = 0.0
            for daily_windows in st_weekly_availability.windows.values():
                for daily_window in daily_windows:
                    assert (
                        daily_window.start.hour  # type: ignore
                        == available_slots.slots[index].start.hour
                    )
                    assert (
                        daily_window.end.hour == available_slots.slots[index].end.hour
                    )
                    index = index + 1
                    delta = dt.timedelta(
                        hours=daily_window.end.hour - daily_window.start.hour,
                        minutes=daily_window.end.minute - daily_window.start.minute,
                        seconds=daily_window.end.second - daily_window.start.second,
                        microseconds=daily_window.end.microsecond
                        - daily_window.start.microsecond,
                    )
                    print(delta)
                    daily_windows_duration = (
                        daily_windows_duration + delta.total_seconds()
                    )

            assert daily_windows_duration == available_slots.total_duration_minutes * 60
            return

        assert len(busy_intervals) > 0, "Should have busy intervals for main test logic"

        for slot in available_slots.slots:
            for busy in busy_intervals:
                overlap = slot.start < busy.end_time and slot.end > busy.start_time
                assert not overlap, (
                    f"Slot {slot.start}-{slot.end} overlaps with busy interval {busy.start_time}-{busy.end_time}"
                )

        for i, slot in enumerate(available_slots.slots):
            for j, slot2 in enumerate(available_slots.slots):
                if i != j:
                    overlap = slot.start < slot2.end and slot.end > slot2.start
                    assert not overlap, (
                        f"Slot {slot.start}-{slot.end} overlaps with slot {slot2.start}-{slot2.end}"
                    )

    def test_get_available_time_slots_window_before_week_start(self):
        """Test that windows before week_start are skipped."""
        # Create availability with a window that ends before week_start
        availability = SchedulerAvailability(
            windows={
                DayOfWeek.MON: [
                    DailyWindowSchema(
                        start=dt.time(8, 0),  # 8 AM
                        end=dt.time(10, 0),  # 10 AM
                    )
                ]
            }
        )

        # Set week_start to 12 PM (after the window ends)
        week_start = dt.datetime(
            2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc
        )  # Monday 12 PM

        available_slots = get_available_time_slots([], availability, week_start, "UTC")

        assert len(available_slots.slots) == 0
        assert available_slots.total_duration_minutes == 0

    def test_get_available_time_slots_week_start_inside_window(self):
        """Test that when week_start is inside a window, the window start is adjusted."""
        availability = SchedulerAvailability(
            windows={
                DayOfWeek.MON: [
                    DailyWindowSchema(
                        start=dt.time(8, 0),  # 8 AM
                        end=dt.time(17, 0),  # 5 PM
                    )
                ]
            }
        )

        # Set week_start to 10 AM (inside the window)
        week_start = dt.datetime(
            2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc
        )  # Monday 10 AM

        available_slots = get_available_time_slots([], availability, week_start, "UTC")

        # Should have one slot from 10 AM to 5 PM (window start adjusted to week_start)
        assert len(available_slots.slots) == 1
        assert available_slots.slots[0].start == week_start
        assert available_slots.slots[0].end == dt.datetime(
            2024, 1, 1, 17, 0, tzinfo=dt.timezone.utc
        )
        assert available_slots.total_duration_minutes == 420  # 7 hours * 60 minutes

    def test_get_available_time_slots_week_start_at_window_end(self):
        """Test edge case where week_start is exactly at window end."""
        availability = SchedulerAvailability(
            windows={
                DayOfWeek.MON: [
                    DailyWindowSchema(
                        start=dt.time(8, 0),  # 8 AM
                        end=dt.time(10, 0),  # 10 AM
                    )
                ]
            }
        )

        # Set week_start to exactly 10 AM (at window end)
        week_start = dt.datetime(
            2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc
        )  # Monday 10 AM

        available_slots = get_available_time_slots([], availability, week_start, "UTC")

        # Should have no available slots since window_end <= week_start
        assert len(available_slots.slots) == 0
        assert available_slots.total_duration_minutes == 0

    def test_get_available_time_slots_multiple_days_with_week_start_adjustment(self):
        """Test multiple days with week_start adjustment on first day."""
        availability = SchedulerAvailability(
            windows={
                DayOfWeek.MON: [
                    DailyWindowSchema(
                        start=dt.time(8, 0),  # 8 AM
                        end=dt.time(17, 0),  # 5 PM
                    )
                ],
                DayOfWeek.TUE: [
                    DailyWindowSchema(
                        start=dt.time(9, 0),  # 9 AM
                        end=dt.time(18, 0),  # 6 PM
                    )
                ],
                DayOfWeek.WED: [
                    DailyWindowSchema(
                        start=dt.time(10, 0),  # 10 AM
                        end=dt.time(19, 0),  # 7 PM
                    )
                ],
            }
        )

        # Set week_start to Tuesday 10 AM (Monday gets skipped, Tuesday gets adjusted)
        week_start = dt.datetime(
            2024, 1, 2, 10, 0, tzinfo=dt.timezone.utc
        )  # Tuesday 10 AM

        available_slots = get_available_time_slots([], availability, week_start, "UTC")

        # Should have slots for:
        # 1. Tuesday: 10 AM - 6 PM (adjusted start time)
        # 2. Wednesday: 10 AM - 7 PM (full day)
        assert len(available_slots.slots) == 2

        # Tuesday slot (adjusted start)
        tuesday_slot = available_slots.slots[0]
        assert tuesday_slot.start == week_start  # 10 AM
        assert tuesday_slot.end == dt.datetime(
            2024, 1, 2, 18, 0, tzinfo=dt.timezone.utc
        )

        # Wednesday slot (full day)
        wednesday_slot = available_slots.slots[1]
        assert wednesday_slot.start == dt.datetime(
            2024, 1, 3, 10, 0, tzinfo=dt.timezone.utc
        )
        assert wednesday_slot.end == dt.datetime(
            2024, 1, 3, 19, 0, tzinfo=dt.timezone.utc
        )

        # Total duration: 8 hours (Tuesday) + 9 hours (Wednesday) = 17 hours = 1020 minutes
        assert available_slots.total_duration_minutes == 1020


class TestPlaceTasksInSlots:
    @given(
        tasks=st.lists(schedulable_task_strategy(), min_size=5, max_size=100),
    )
    def test_remove_task_from_deque(self, tasks: list[SchedulableTask]) -> None:
        unique_tasks = {task.id: task for task in tasks}
        tasks = list[SchedulableTask](unique_tasks.values())
        task_index = random.randint(0, len(tasks) - 1)
        task = tasks[task_index]
        tasks_deque = deque[SchedulableTask](tasks)
        _remove_task_from_deque(tasks_deque, task)
        assert len(tasks_deque) == len(tasks) - 1
        tasks.remove(task)
        for task in tasks:
            assert task == tasks_deque.popleft()

    @given(
        available_slots_strategy(),
        st.lists(schedulable_task_strategy(), min_size=1, max_size=100),
    )
    def test_place_tasks_in_slots_no_splitting(
        self,
        available_slots: AvailableSlots,
        tasks: list[SchedulableTask],
    ):
        unique_tasks = {task.id: task for task in tasks}
        tasks = list(unique_tasks.values())
        ranked_tasks = rank_tasks(tasks, now_utc())
        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            ranked_tasks, available_slots, split_tasks=False
        )
        assert len(schedule_blocks) + len(unscheduled_tasks) == len(tasks)
        # Check that every task is either scheduled or unscheduled
        for schedule_block in schedule_blocks:
            assert schedule_block.task_id in [
                task.id for task in tasks if task not in unscheduled_tasks
            ]
            assert schedule_block.start_time >= available_slots.slots[0].start
            assert schedule_block.end_time <= available_slots.slots[-1].end
        for unscheduled_task in unscheduled_tasks:
            assert unscheduled_task.id in [
                task.id for task in tasks if task not in schedule_blocks
            ]

        scheduled_tasks_durations = 0
        for schedule_block in schedule_blocks:
            assert schedule_block.start_time < schedule_block.end_time
            in_slot = False
            for slot in available_slots.slots:
                if (
                    schedule_block.start_time >= slot.start
                    and schedule_block.end_time <= slot.end
                ):
                    in_slot = True
                    break
            assert in_slot, (
                f"Schedule block {schedule_block.start_time}-{schedule_block.end_time} not in any slot"
            )
            scheduled_tasks_durations += (
                schedule_block.end_time - schedule_block.start_time
            ).total_seconds() / 60

        remaining_slots = get_remaining_free_slots(available_slots, schedule_blocks)

        remaining_duration = remaining_slots.total_duration_minutes
        total_used_duration = scheduled_tasks_durations
        original_duration = available_slots.total_duration_minutes

        assert total_used_duration + remaining_duration == original_duration, (
            f"Time mismatch: used={total_used_duration}min, remaining={remaining_duration}min, "
            f"original={original_duration}min"
        )

        assert scheduled_tasks_durations <= available_slots.total_duration_minutes

    @given(
        available_slots_strategy(),
        st.lists(schedulable_task_strategy(), min_size=1, max_size=100),
    )
    def test_place_tasks_in_slots_with_splitting(
        self,
        available_slots: AvailableSlots,
        tasks: list[SchedulableTask],
    ):
        unique_tasks = {task.id: task for task in tasks}
        tasks = list(unique_tasks.values())
        ranked_tasks = rank_tasks(tasks, now_utc())
        sum_expected_duration_minutes = sum(
            task.expected_duration_minutes for task in tasks
        )
        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            ranked_tasks, available_slots, split_tasks=True
        )
        first_slot_duration_minutes = available_slots.slots[0].duration_minutes
        # if tasks don't fit in the first slot, they should be split
        # thus increasing the number of tasks by at least 1
        if sum_expected_duration_minutes > first_slot_duration_minutes:
            assert len(schedule_blocks) + len(unscheduled_tasks) > len(tasks)

        sum_schedule_blocks_duration_minutes = sum(
            (schedule_block.end_time - schedule_block.start_time).total_seconds() / 60
            for schedule_block in schedule_blocks
        )
        sum_unscheduled_tasks_duration_minutes = sum(
            task.expected_duration_minutes for task in unscheduled_tasks
        )
        assert (
            sum_schedule_blocks_duration_minutes
            + sum_unscheduled_tasks_duration_minutes
            == sum_expected_duration_minutes
        )
        for schedule_block in schedule_blocks:
            assert schedule_block.start_time < schedule_block.end_time
            in_slot = False
            for slot in available_slots.slots:
                if (
                    schedule_block.start_time >= slot.start
                    and schedule_block.end_time <= slot.end
                ):
                    in_slot = True
                    break
            assert in_slot, (
                f"Schedule block {schedule_block.start_time}-{schedule_block.end_time} not in any slot"
            )
        for unscheduled_task in unscheduled_tasks:
            assert unscheduled_task.id in [
                task.id for task in tasks if task not in schedule_blocks
            ]

    def test_place_tasks_empty_slots(self):
        """Test placing tasks when there are no available slots."""
        tasks = [
            SchedulableTask(
                id=1, title="Task 1", expected_duration_minutes=60, priority=1
            )
        ]
        empty_slots = AvailableSlots(slots=[])

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            tasks, empty_slots, split_tasks=False
        )

        assert len(schedule_blocks) == 0
        assert len(unscheduled_tasks) == 1
        assert unscheduled_tasks[0].id == 1

    def test_place_tasks_empty_task_list(self):
        """Test placing tasks when there are no tasks to schedule."""
        empty_tasks: list[SchedulableTask] = []
        slots = AvailableSlots(
            slots=[
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(2024, 1, 1, 17, 0, tzinfo=dt.timezone.utc),
                )
            ]
        )

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            empty_tasks, slots, split_tasks=False
        )

        assert len(schedule_blocks) == 0
        assert len(unscheduled_tasks) == 0

    def test_place_tasks_exact_fit(self):
        """Test placing a task that fits exactly in a slot."""
        tasks = [
            SchedulableTask(
                id=1,
                title="Exact Fit Task",
                expected_duration_minutes=120,  # 2 hours
                priority=1,
            )
        ]
        slots = AvailableSlots(
            slots=[
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(
                        2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc
                    ),  # Exactly 2 hours
                )
            ]
        )

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            tasks, slots, split_tasks=False
        )

        assert len(schedule_blocks) == 1
        assert len(unscheduled_tasks) == 0
        assert schedule_blocks[0].task_id == 1
        assert schedule_blocks[0].start_time == slots.slots[0].start
        assert schedule_blocks[0].end_time == slots.slots[0].end

    def test_place_tasks_multiple_slots(self):
        """Test placing tasks across multiple slots."""
        tasks = [
            SchedulableTask(
                id=1, title="Task 1", expected_duration_minutes=60, priority=1
            ),
            SchedulableTask(
                id=2, title="Task 2", expected_duration_minutes=90, priority=2
            ),
            SchedulableTask(
                id=3, title="Task 3", expected_duration_minutes=30, priority=3
            ),
        ]
        slots = AvailableSlots(
            slots=[
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(
                        2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc
                    ),  # 1 hour
                ),
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(
                        2024, 1, 1, 12, 30, tzinfo=dt.timezone.utc
                    ),  # 1.5 hours
                ),
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 14, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(
                        2024, 1, 1, 15, 0, tzinfo=dt.timezone.utc
                    ),  # 1 hour
                ),
            ]
        )

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            tasks, slots, split_tasks=False
        )

        assert len(schedule_blocks) == 3
        assert len(unscheduled_tasks) == 0

        # Check that tasks are scheduled in order
        assert schedule_blocks[0].task_id == 1  # 60 min task in first slot
        assert schedule_blocks[1].task_id == 2  # 90 min task in second slot
        assert schedule_blocks[2].task_id == 3  # 30 min task in third slot

    def test_place_tasks_splitting_enabled(self):
        """Test task splitting when enabled."""
        tasks = [
            SchedulableTask(
                id=1,
                title="Long Task",
                expected_duration_minutes=180,  # 3 hours
                priority=1,
            )
        ]
        slots = AvailableSlots(
            slots=[
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(
                        2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc
                    ),  # 2 hours
                )
            ]
        )

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            tasks, slots, split_tasks=True
        )

        assert len(schedule_blocks) == 1
        assert len(unscheduled_tasks) == 1  # The remainder of the split task

        # Check that the scheduled portion is exactly 2 hours
        scheduled_block = schedule_blocks[0]
        assert scheduled_block.task_id == 1
        assert (
            scheduled_block.end_time - scheduled_block.start_time
        ).total_seconds() / 60 == 120

        # Check that the unscheduled portion is 1 hour
        unscheduled_task = unscheduled_tasks[0]
        assert unscheduled_task.id == 1  # Same task ID
        assert unscheduled_task.expected_duration_minutes == 60

    def test_place_tasks_splitting_disabled_find_smaller(self):
        """Test finding a smaller task when splitting is disabled."""
        tasks = [
            SchedulableTask(
                id=1,
                title="Long Task",
                expected_duration_minutes=180,  # 3 hours - too big
                priority=1,
            ),
            SchedulableTask(
                id=2,
                title="Short Task",
                expected_duration_minutes=60,  # 1 hour - fits
                priority=2,
            ),
        ]
        slots = AvailableSlots(
            slots=[
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(
                        2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc
                    ),  # 2 hours
                )
            ]
        )

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            tasks, slots, split_tasks=False
        )

        assert len(schedule_blocks) == 1
        assert len(unscheduled_tasks) == 1  # Both tasks remain unscheduled
        # This will fail

        # The smaller task should be scheduled
        assert schedule_blocks[0].task_id == 2

    def test_place_tasks_splitting_disabled_no_fitting_task(self):
        """Test when no task fits and splitting is disabled."""
        tasks = [
            SchedulableTask(
                id=1,
                title="Long Task 1",
                expected_duration_minutes=180,  # 3 hours
                priority=1,
            ),
            SchedulableTask(
                id=2,
                title="Long Task 2",
                expected_duration_minutes=240,  # 4 hours
                priority=2,
            ),
        ]
        slots = AvailableSlots(
            slots=[
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(
                        2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc
                    ),  # 2 hours
                )
            ]
        )

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            tasks, slots, split_tasks=False
        )

        assert len(schedule_blocks) == 0
        assert len(unscheduled_tasks) == 2

    def test_place_tasks_partial_slot_usage(self):
        """Test when a task doesn't fill the entire slot."""
        tasks = [
            SchedulableTask(
                id=1,
                title="Short Task",
                expected_duration_minutes=30,
                priority=1,
            )
        ]
        slots = AvailableSlots(
            slots=[
                TimeSlot(
                    start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
                    end=dt.datetime(2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc),
                )
            ]
        )

        schedule_blocks, unscheduled_tasks = place_tasks_in_slots(
            tasks, slots, split_tasks=False
        )

        assert len(schedule_blocks) == 1
        assert len(unscheduled_tasks) == 0

        # Task should be scheduled at the beginning of the slot
        assert schedule_blocks[0].start_time == slots.slots[0].start
        assert (
            schedule_blocks[0].end_time - schedule_blocks[0].start_time
        ).total_seconds() / 60 == 30

    def test_create_schedule_block(self):
        """Test the _create_schedule_block helper function."""
        task = SchedulableTask(
            id=1,
            title="Test Task",
            description="Test Description",
            expected_duration_minutes=60,
            priority=1,
        )
        start_time = dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc)

        block = _create_schedule_block(task, start_time)

        assert block.task_id == 1
        assert block.start_time == start_time
        assert block.end_time == start_time + dt.timedelta(minutes=60)
        assert block.source == "task"
        assert block.title == "Test Task"
        assert block.description == "Test Description"

    def test_fill_single_slot_exact_fit(self):
        """Test _fill_single_slot with a task that fits exactly."""
        slot = TimeSlot(
            start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc),
        )
        tasks = deque(
            [
                SchedulableTask(
                    id=1,
                    title="Exact Fit Task",
                    expected_duration_minutes=60,  # Exactly 1 hour
                    priority=1,
                )
            ]
        )

        blocks = _fill_single_slot(slot, tasks, split_tasks=False)

        assert len(blocks) == 1
        assert len(tasks) == 0  # Task should be consumed
        assert blocks[0].task_id == 1
        assert blocks[0].start_time == slot.start
        assert blocks[0].end_time == slot.end

    def test_fill_single_slot_partial_fit_no_splitting(self):
        """Test _fill_single_slot when task doesn't fit and splitting is disabled."""
        slot = TimeSlot(
            start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc),
        )
        tasks = deque(
            [
                SchedulableTask(
                    id=1,
                    title="Long Task",
                    expected_duration_minutes=120,
                    priority=1,
                )
            ]
        )

        blocks = _fill_single_slot(slot, tasks, split_tasks=False)

        assert len(blocks) == 0
        assert len(tasks) == 1
        assert tasks[0].id == 1

    def test_fill_single_slot_with_splitting(self):
        """Test _fill_single_slot with task splitting enabled."""
        slot = TimeSlot(
            start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc),
        )
        tasks = deque(
            [
                SchedulableTask(
                    id=1,
                    title="Long Task",
                    expected_duration_minutes=120,
                    priority=1,
                )
            ]
        )

        blocks = _fill_single_slot(slot, tasks, split_tasks=True)

        assert len(blocks) == 1
        assert len(tasks) == 1
        assert blocks[0].task_id == 1
        assert blocks[0].start_time == slot.start
        assert blocks[0].end_time == slot.end
        assert tasks[0].expected_duration_minutes == 60

    def test_fill_single_slot_multiple_tasks(self):
        """Test _fill_single_slot with multiple tasks."""
        slot = TimeSlot(
            start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc),
        )
        tasks = deque(
            [
                SchedulableTask(
                    id=1,
                    title="Task 1",
                    expected_duration_minutes=60,
                    priority=1,
                ),
                SchedulableTask(
                    id=2,
                    title="Task 2",
                    expected_duration_minutes=30,
                    priority=2,
                ),
            ]
        )

        blocks = _fill_single_slot(slot, tasks, split_tasks=False)

        assert len(blocks) == 2  # Both tasks should fit
        assert len(tasks) == 0  # All tasks consumed
        assert blocks[0].task_id == 1
        assert blocks[1].task_id == 2
        assert blocks[0].start_time == slot.start
        assert blocks[0].end_time == slot.start + dt.timedelta(minutes=60)
        assert blocks[1].start_time == slot.start + dt.timedelta(minutes=60)
        assert blocks[1].end_time == slot.start + dt.timedelta(minutes=90)

    def test_fill_single_slot_empty_tasks(self):
        """Test _fill_single_slot with no tasks."""
        slot = TimeSlot(
            start=dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc),
        )
        tasks: deque[SchedulableTask] = deque()

        blocks = _fill_single_slot(slot, tasks, split_tasks=False)

        assert len(blocks) == 0
        assert len(tasks) == 0

    def test_find_best_fitting_task(self):
        """Test _find_best_fitting_task helper function."""
        tasks = deque(
            [
                SchedulableTask(
                    id=1,
                    title="Long Task",
                    expected_duration_minutes=120,
                    priority=1,
                ),
                SchedulableTask(
                    id=2,
                    title="Medium Task",
                    expected_duration_minutes=90,
                    priority=2,
                ),
                SchedulableTask(
                    id=3,
                    title="Short Task",
                    expected_duration_minutes=30,
                    priority=3,
                ),
            ]
        )

        fitting_task = _find_best_fitting_task(tasks, 60)
        assert fitting_task is not None
        assert fitting_task.id == 3

        fitting_task = _find_best_fitting_task(tasks, 90)
        assert fitting_task is not None
        assert fitting_task.id == 2

        fitting_task = _find_best_fitting_task(tasks, 120)
        assert fitting_task is not None
        assert fitting_task.id == 1

    def test_find_best_fitting_task_no_fit(self):
        """Test _find_best_fitting_task when no task fits."""
        tasks = deque(
            [
                SchedulableTask(
                    id=1,
                    title="Long Task",
                    expected_duration_minutes=120,
                    priority=1,
                ),
                SchedulableTask(
                    id=2,
                    title="Medium Task",
                    expected_duration_minutes=90,
                    priority=2,
                ),
            ]
        )

        # Find task that fits in 30 minutes
        fitting_task = _find_best_fitting_task(tasks, 30)
        assert fitting_task is None  # No task should fit

    def test_find_best_fitting_task_empty_deque(self):
        """Test _find_best_fitting_task with empty deque."""
        tasks: deque[SchedulableTask] = deque[SchedulableTask]()

        fitting_task = _find_best_fitting_task(tasks, 60)
        assert fitting_task is None

    def test_remove_task_from_deque_edge_cases(self):
        """Test _remove_task_from_deque with various edge cases."""
        # Test removing from single-item deque
        tasks = deque(
            [
                SchedulableTask(
                    id=1, title="Task 1", expected_duration_minutes=60, priority=1
                )
            ]
        )
        task_to_remove = tasks[0]
        _remove_task_from_deque(tasks, task_to_remove)
        assert len(tasks) == 0

        # Test removing from empty deque
        tasks: deque[SchedulableTask] = deque[SchedulableTask]()
        task_to_remove = SchedulableTask(
            id=1, title="Task 1", expected_duration_minutes=60, priority=1
        )
        _remove_task_from_deque(tasks, task_to_remove)
        assert len(tasks) == 0

        # Test removing non-existent task
        tasks = deque(
            [
                SchedulableTask(
                    id=1, title="Task 1", expected_duration_minutes=60, priority=1
                ),
                SchedulableTask(
                    id=2, title="Task 2", expected_duration_minutes=60, priority=1
                ),
            ]
        )
        original_length = len(tasks)
        non_existent_task = SchedulableTask(
            id=3, title="Task 3", expected_duration_minutes=60, priority=1
        )
        _remove_task_from_deque(tasks, non_existent_task)
        assert len(tasks) == original_length


class TestSchedulingCore:
    def test_schedule_tasks_main_function(
        self,
        task_list: list[Task],
        schedule_item_list: list[ScheduleItem],
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
    ):
        """Test the main schedule_tasks function that serves as the API entry point."""
        response = schedule_tasks(
            task_list, schedule_item_list, weekly_availability, SchedulingConfig()
        )

        assert isinstance(response, SchedulingResponse)
        assert isinstance(response.schedule_blocks, list)
        assert isinstance(response.warnings, list)

        for block in response.schedule_blocks:
            assert block.task_id is not None
            assert block.start_time is not None
            assert block.end_time is not None
            assert block.start_time < block.end_time
            assert block.source == "task"

    def test_schedule_core_algorithm(
        self,
        task_list: list[Task],
        schedule_item_list: list[ScheduleItem],
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
    ):
        """Test the core schedule function with a SchedulingRequest."""
        schedulable_tasks = tasks_to_schedulables(task_list)
        busy_intervals = schedule_items_to_busy_intervals(schedule_item_list)
        scheduler_availability = SchedulerAvailability.model_validate(
            weekly_availability
        )
        start_time = dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc)

        request = SchedulingRequest(
            tasks=schedulable_tasks,
            busy_intervals=busy_intervals,
            scheduler_availability=scheduler_availability,
            config=SchedulingConfig(),
            start_time=start_time,
            user_timezone="UTC",
        )

        response = schedule(request)

        assert isinstance(response, SchedulingResponse)
        assert isinstance(response.schedule_blocks, list)
        assert isinstance(response.warnings, list)

    def test_schedule_empty_tasks_with_daily_windows(
        self,
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
    ):
        """Test scheduling with no tasks."""
        empty_tasks: list[Task] = []
        empty_schedule_items: list[ScheduleItem] = []

        response = schedule_tasks(
            empty_tasks, empty_schedule_items, weekly_availability, "UTC"
        )

        assert len(response.schedule_blocks) == 0
        assert len(response.warnings) == 0

    def test_schedule_empty_tasks_without_daily_windows(
        self,
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
    ):
        """Test scheduling with no tasks."""
        empty_tasks: list[Task] = []
        empty_schedule_items: list[ScheduleItem] = []

        response = schedule_tasks(
            empty_tasks, empty_schedule_items, weekly_availability, "UTC"
        )

        assert len(response.schedule_blocks) == 0
        assert len(response.warnings) == 0

    def test_schedule_no_availability(
        self, task_list: list[Task], schedule_item_list: list[ScheduleItem]
    ):
        """Test scheduling with no availability windows."""
        empty_availability: WeeklyAvailability = WeeklyAvailability(windows=[])

        response = schedule_tasks(
            task_list, schedule_item_list, empty_availability, SchedulingConfig()
        )

        # All tasks should be unscheduled due to no availability
        assert len(response.schedule_blocks) == 0
        assert len(response.warnings) == len(task_list)

    def test_schedule_with_custom_config(
        self,
        task_list: list[Task],
        schedule_item_list: list[ScheduleItem],
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
    ):
        """Test schedule function with custom configuration."""
        schedulable_tasks = tasks_to_schedulables(task_list)
        busy_intervals = schedule_items_to_busy_intervals(schedule_item_list)
        scheduler_availability = SchedulerAvailability.model_validate(
            weekly_availability,
        )
        start_time = dt.datetime(2024, 1, 1, 9, 0, tzinfo=dt.timezone.utc)

        request = SchedulingRequest(
            tasks=schedulable_tasks,
            busy_intervals=busy_intervals,
            scheduler_availability=scheduler_availability,
            config=SchedulingConfig(allow_splitting=False),
            start_time=start_time,
            user_timezone="UTC",
        )

        response = schedule(request)

        assert isinstance(response, SchedulingResponse)
        # Verify that the response contains the expected structure
        assert hasattr(response, "schedule_blocks")
        assert hasattr(response, "warnings")

    def test_schedule_tasks_with_deadlines(
        self,
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
    ):
        """Test schedule_tasks with tasks that have deadlines."""
        tasks_with_deadlines = [
            Task(
                id=1,
                title="Urgent Task",
                description="Urgent Task",
                expected_duration_minutes=60,
                priority=1,
                deadline=dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc),
            ),
            Task(
                id=2,
                title="Regular Task",
                description="Regular Task",
                expected_duration_minutes=90,
                priority=2,
                deadline=None,
            ),
        ]
        empty_schedule_items: list[ScheduleItem] = []

        response = schedule_tasks(
            tasks_with_deadlines,
            empty_schedule_items,
            weekly_availability,
            SchedulingConfig(),
        )

        assert isinstance(response, SchedulingResponse)
        # The urgent task should be scheduled first due to deadline
        if response.schedule_blocks:
            # Check that tasks are scheduled in priority order (deadline first)
            scheduled_task_ids = [block.task_id for block in response.schedule_blocks]
            if 1 in scheduled_task_ids and 2 in scheduled_task_ids:
                urgent_index = scheduled_task_ids.index(1)
                regular_index = scheduled_task_ids.index(2)
                assert urgent_index < regular_index

    def test_schedule_tasks_with_mixed_timezones(
        self,
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
    ):
        """Test schedule_tasks with tasks that have different timezone handling."""
        tasks_with_timezones = [
            Task(
                id=1,
                title="UTC Task",
                description="UTC Task",
                expected_duration_minutes=60,
                priority=1,
                deadline=dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc),
            ),
            Task(
                id=2,
                title="Naive Task",
                description="Naive Task",
                expected_duration_minutes=90,
                priority=2,
                deadline=dt.datetime(2024, 1, 1, 15, 0),  # No timezone
            ),
        ]
        empty_schedule_items: list[ScheduleItem] = []

        response = schedule_tasks(
            tasks_with_timezones,
            empty_schedule_items,
            weekly_availability,
            SchedulingConfig(),
        )

        assert isinstance(response, SchedulingResponse)
        # Should handle timezone conversion properly
        for block in response.schedule_blocks:
            assert block.start_time.tzinfo is not None
            assert block.end_time.tzinfo is not None

    def test_schedule_with_overlapping_busy_intervals(
        self,
        task_list: list[Task],
        weekly_availability: WeeklyAvailability,
        daily_windows: list[DailyWindowSchema],
        user: User,
    ):
        """Test scheduling with overlapping busy intervals."""
        overlapping_schedule_items = [
            ScheduleItem(
                id=1,
                user_id=user.id,  # type: ignore[attr-defined]
                task_id=1,
                start_time=dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc),
                end_time=dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc),
                title="Meeting 1",
                description="Meeting 1",
            ),
            ScheduleItem(
                id=2,
                user_id=user.id,  # type: ignore[attr-defined]
                task_id=2,
                start_time=dt.datetime(
                    2024, 1, 1, 11, 0, tzinfo=dt.timezone.utc
                ),  # Overlaps with Meeting 1
                end_time=dt.datetime(2024, 1, 1, 13, 0, tzinfo=dt.timezone.utc),
                title="Meeting 2",
                description="Meeting 2",
            ),
        ]

        response = schedule_tasks(
            task_list,
            overlapping_schedule_items,
            weekly_availability,
            SchedulingConfig(),
        )

        assert isinstance(response, SchedulingResponse)
