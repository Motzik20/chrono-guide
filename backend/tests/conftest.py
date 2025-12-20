import datetime as dt
from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.timezone import get_next_weekday, now_utc
from app.models.availability import DailyWindowModel, WeeklyAvailability
from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.models.user import User
from app.schemas.availability import DailyWindow as DailyWindowSchema
from app.schemas.availability import DayOfWeek
from app.schemas.task import TaskDraft
from app.services.scheduling_service import (
    AvailableSlots,
    BusyInterval,
    SchedulableTask,
    SchedulerAvailability,
    TimeSlot,
    schedule_item_to_busy_interval,
)


@pytest.fixture
def engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def user(session: Session) -> User:
    user = User(email="test-example@mail.com", password="example_hash_password")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def task(session: Session, user: User) -> Task:
    task = Task(
        user_id=user.id, # type: ignore[attr-defined]
        title="Test Task",
        description="This is a task only for test purposes",
        expected_duration_minutes=60,
        priority=2,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def longer_task(session: Session, user: User) -> Task:
    task = Task(
        user_id=user.id, # type: ignore[attr-defined]
        title="Test Task with longer duration",
        description="This is a task only for test purposes",
        expected_duration_minutes=120,
        priority=2,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def deadline_task(session: Session, user: User) -> Task:
    tomorrow: dt.datetime = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
    deadline = tomorrow.replace(
        hour=14, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
    )
    task = Task(
        user_id=user.id, # type: ignore[attr-defined]
        title="Test with deadline",
        description="This taks is a simple task with a deadline",
        expected_duration_minutes=60,
        priority=2,
        deadline=deadline,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def later_deadline_task(session: Session, user: User) -> Task:
    tomorrow: dt.datetime = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)
    deadline = tomorrow.replace(
        hour=14, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
    )
    task = Task(
        user_id=user.id,  # type: ignore[attr-defined]
        title="Test with later deadline",
        description="This taks is a simple task with a deadline",
        expected_duration_minutes=60,
        priority=2,
        deadline=deadline,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def urgent_later_deadline_task(session: Session, user: User) -> Task:
    tomorrow: dt.datetime = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)
    deadline = tomorrow.replace(
        hour=14, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
    )
    task = Task(
        user_id=user.id,  # type: ignore[attr-defined]
        title="urgent Test with later deadline",
        description="This taks is a simple task with a deadline",
        expected_duration_minutes=60,
        priority=0,
        deadline=deadline,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def urgent_task(session: Session, user: User) -> Task:
    task = Task(
        user_id=user.id,  # type: ignore[attr-defined]
        title="urgent Test Task",
        description="This taks is a simple task with a deadline",
        expected_duration_minutes=60,
        priority=0,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def task_list(
    task: Task,
    urgent_task: Task,
    longer_task: Task,
    deadline_task: Task,
    later_deadline_task: Task,
    urgent_later_deadline_task: Task,
) -> list[Task]:
    """Return a list of all task fixtures for testing."""
    return [
        task,
        urgent_task,
        longer_task,
        deadline_task,
        later_deadline_task,
        urgent_later_deadline_task,
    ]


@pytest.fixture
def schedule_item(session: Session, user: User, task: Task) -> ScheduleItem:
    tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
    start_time = tomorrow.replace(
        hour=9, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
    )
    end_time = start_time + dt.timedelta(hours=2)

    schedule_item = ScheduleItem(
        user_id=user.id,  # type: ignore[attr-defined]
        task_id=task.id,  # type: ignore[attr-defined]
        start_time=start_time,
        end_time=end_time,
        source="task",
        title="Scheduled Task",
    )
    session.add(schedule_item)
    session.commit()
    session.refresh(schedule_item)
    return schedule_item


@pytest.fixture
def schedule_item_list(session: Session, user: User) -> list[ScheduleItem]:
    tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
    start_time = tomorrow.replace(
        hour=9, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
    )
    end_time = start_time + dt.timedelta(hours=2)
    schedule_items: list[ScheduleItem] = []
    for i in range(10):
        schedule_item = ScheduleItem(
            user_id=user.id,  # type: ignore[attr-defined]
            task_id=None,
            start_time=start_time + dt.timedelta(days=i),
            end_time=end_time + dt.timedelta(days=i),
            source="task",
            title="Scheduled Task",
        )
        session.add(schedule_item)
        session.commit()
        session.refresh(schedule_item)
        schedule_items.append(schedule_item)
    return schedule_items


@pytest.fixture
def weekly_availability(session: Session, user: User) -> WeeklyAvailability:
    availability = WeeklyAvailability(user_id=user.id)  # type: ignore[attr-defined]
    session.add(availability)
    session.commit()
    session.refresh(availability)
    return availability


@pytest.fixture
def daily_windows(session: Session, weekly_availability: WeeklyAvailability) -> None:
    first_start_time = dt.time(hour=7, minute=0)
    first_end_time = dt.time(hour=12, minute=0)
    second_start_time = dt.time(hour=13, minute=0)
    second_end_time = dt.time(hour=17, minute=0)
    for i in range(7):
        first_daily_window = DailyWindowModel(
            weekly_availability_id=weekly_availability.id,  # type: ignore[attr-defined]
            day_of_week=i,
            start_time=first_start_time,
            end_time=first_end_time,
        )
        second_daily_window = DailyWindowModel(
            weekly_availability_id=weekly_availability.id,  # type: ignore[attr-defined]
            day_of_week=i,
            start_time=second_start_time,
            end_time=second_end_time,
        )
        session.add(first_daily_window)
        session.add(second_daily_window)
        session.commit()
        session.refresh(first_daily_window)
        session.refresh(second_daily_window)

    # Refresh weekly_availability to load the relationships
    session.refresh(weekly_availability)


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    from app.app_factory import create_app
    from app.core.db import get_db

    app = create_app(local=True)

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def busy_interval(schedule_item: ScheduleItem) -> BusyInterval:
    busy_interval = schedule_item_to_busy_interval(schedule_item)
    return busy_interval


@pytest.fixture
def daily_window_start():
    tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
    start_time = tomorrow.replace(
        hour=7, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
    )
    return start_time


@pytest.fixture
def daily_window_end():
    tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
    end_time = tomorrow.replace(
        hour=13, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc
    )
    return end_time

@pytest.fixture
def mock_task_drafts() -> list[TaskDraft]:
    """Mock task drafts returned by ChronoAgent."""
    return [
        TaskDraft(
            title="Test Task 1",
            description="First test task",
            expected_duration_minutes=60,
            tips=["Tip 1", "Tip 2"],
        ),
        TaskDraft(
            title="Test Task 2",
            description="Second test task",
            expected_duration_minutes=30,
            tips=[],
        ),
    ]

@pytest.fixture
def mock_chrono_agent(client: TestClient, mock_task_drafts: list[TaskDraft]) -> Generator[AsyncMock, None, None]:
    """Fixture that mocks ChronoAgent for a test."""
    from app.api.routers.tasks import get_chrono_agent

    app = client.app
    mock_agent = AsyncMock()
    mock_agent.analyze_tasks_from_file = AsyncMock(return_value=mock_task_drafts)
    mock_agent.analyze_tasks_from_text = AsyncMock(return_value=mock_task_drafts)

    app.dependency_overrides[get_chrono_agent] = lambda: mock_agent  # type: ignore[attr-defined]
    yield mock_agent
    app.dependency_overrides.pop(get_chrono_agent, None)  # type: ignore[attr-defined]

@pytest.fixture
def mock_user_id(client: TestClient) -> Generator[int, None, None]:
    from app.core.auth import get_current_user_id
    app = client.app
    app.dependency_overrides[get_current_user_id] = lambda: 1# type: ignore[attr-defined]
    yield 1
    app.dependency_overrides.pop(get_current_user_id, None)# type: ignore[attr-defined]

@st.composite
def datetime_strategy(
    draw: "DrawFn",
    min_date: dt.datetime | None = None,
    max_date: dt.datetime | None = None,
    timezone_aware: bool = True,
) -> dt.datetime:
    """Generate realistic datetime objects for testing."""
    from app.core.timezone import ensure_utc

    # Use a fixed reference point to avoid non-deterministic datetime.now() calls
    base_date = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)

    if min_date is None:
        min_date = base_date - dt.timedelta(days=30)
    if max_date is None:
        max_date = min_date + dt.timedelta(days=365)

    min_naive = min_date.replace(tzinfo=None) if min_date else None
    max_naive = max_date.replace(tzinfo=None) if max_date else None

    # Generate random datetime
    if min_naive is None or max_naive is None:
        raise ValueError("min_date and max_date must be provided or calculable")
    random_datetime = draw(
        st.datetimes(
            min_value=min_naive,
            max_value=max_naive,
        )
    )
    if timezone_aware:
        result = ensure_utc(random_datetime)
        if result is None:
            raise ValueError("ensure_utc returned None")
        random_datetime = result

    # Round to nearest minute for cleaner testing
    return random_datetime.replace(second=0, microsecond=0)


@st.composite
def time_window_strategy(
    draw: "DrawFn", min_hour: int = 0, max_hour: int = 23
) -> tuple[dt.time, dt.time]:
    """Generate realistic time windows (start_time, end_time)."""
    start_hour = draw(st.integers(min_value=min_hour, max_value=max_hour - 2))
    end_hour = draw(st.integers(min_value=start_hour + 1, max_value=max_hour))

    start_minute = draw(st.sampled_from([0, 15, 30, 45]))
    end_minute = draw(st.sampled_from([0, 15, 30, 45]))

    start_time = dt.time(hour=start_hour, minute=start_minute)
    end_time = dt.time(hour=end_hour, minute=end_minute)

    return start_time, end_time


@st.composite
def busy_interval_strategy(
    draw: "DrawFn",
    min_date: dt.datetime | None = None,
    max_date: dt.datetime | None = None,
) -> BusyInterval:
    """Generate realistic BusyInterval objects for testing."""
    start_time = draw(datetime_strategy(min_date, max_date))

    # Duration between 15 minutes and 8 hours
    duration_minutes = draw(st.integers(min_value=15, max_value=480))
    end_time = start_time + dt.timedelta(minutes=duration_minutes)

    # Ensure end_time is after start_time and within bounds
    if max_date and end_time > max_date:
        end_time = max_date

    return BusyInterval(
        task_id=draw(st.integers(min_value=1, max_value=1000)),
        start_time=start_time,
        end_time=end_time,
        title=draw(st.text(min_size=1, max_size=50)),
    )


@st.composite
def busy_intervals_strategy(
    draw: "DrawFn",
    min_count: int = 0,
    max_count: int = 10,
    min_date: dt.datetime | None = None,
    max_date: dt.datetime | None = None,
) -> list[BusyInterval]:
    count = draw(st.integers(min_value=min_count, max_value=max_count))

    if count == 0:
        return []

    intervals: list[BusyInterval] = []
    for _ in range(count):
        interval = draw(busy_interval_strategy(min_date=min_date, max_date=max_date))
        intervals.append(interval)

    return intervals


@st.composite
def schedulable_task_strategy(draw: "DrawFn") -> SchedulableTask:
    """Generate realistic SchedulableTask objects for testing."""
    # Use a fixed reference point to avoid non-deterministic datetime.now() calls
    base_date = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)

    return SchedulableTask(
        id=draw(st.integers(min_value=1, max_value=1000)),
        title=draw(st.text(min_size=1, max_size=100)),
        expected_duration_minutes=draw(st.integers(min_value=15, max_value=480)),
        deadline=draw(
            st.one_of(
                st.none(),
                datetime_strategy(
                    min_date=base_date + dt.timedelta(days=1),
                    max_date=base_date + dt.timedelta(days=30),
                ),
            )
        ),
        priority=draw(st.integers(min_value=0, max_value=4)),
    )


@st.composite
def weekly_availability_strategy(draw: "DrawFn") -> SchedulerAvailability:
    """Generate realistic WeeklyAvailability objects for testing."""
    windows: dict[DayOfWeek, list[DailyWindowSchema]] = {}

    # Generate windows for some random days (not necessarily all 7)
    num_days = draw(st.integers(min_value=1, max_value=7))
    selected_days = draw(
        st.sets(st.sampled_from(list(DayOfWeek)), min_size=num_days, max_size=7)
    )

    for day in selected_days:
        # Generate 1-3 time windows per day
        num_windows = draw(st.integers(min_value=1, max_value=3))
        day_windows: list[DailyWindowSchema] = []

        for _ in range(num_windows):
            start_time, end_time = draw(time_window_strategy())
            schema = DailyWindowSchema(start=start_time, end=end_time)
            overlap = False
            for day_window in day_windows:
                overlap = (
                    schema.start < day_window.end and schema.end > day_window.start
                )
                if overlap:
                    break
            if not overlap:
                day_windows.append(schema)

        windows[day] = day_windows
    return SchedulerAvailability(windows=windows)


@st.composite
def time_slot_strategy(draw: "DrawFn", min_start: dt.datetime) -> TimeSlot:
    """Generate realistic TimeSlot objects for testing."""
    # Random offset between 30 minutes and 10 hours for duration
    random_offset = draw(st.integers(min_value=30, max_value=600))
    return TimeSlot(
        start=draw(
            datetime_strategy(
                min_date=min_start,
                max_date=min_start + dt.timedelta(minutes=random_offset - 15),
            )
        ),
        end=draw(
            datetime_strategy(
                min_date=min_start + dt.timedelta(minutes=random_offset),
                max_date=min_start + dt.timedelta(minutes=random_offset + 15),
            )
        ),
    )


@st.composite
def available_slots_strategy(draw: "DrawFn") -> AvailableSlots:
    """Generate realistic AvailableSlots objects for testing."""
    amount_of_slots = draw(st.integers(min_value=1, max_value=21))
    min_start = get_next_weekday(now_utc())
    slots: list[TimeSlot] = []
    for _ in range(amount_of_slots):
        slot = draw(time_slot_strategy(min_start=min_start))
        min_start = slot.end
        slots.append(slot)
    return AvailableSlots(slots=slots)

