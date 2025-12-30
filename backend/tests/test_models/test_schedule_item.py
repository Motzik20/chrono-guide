import datetime as dt

import pytest
from sqlmodel import Session

from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.models.user import User
from app.schemas.schedule_item import (
    ScheduleItemCreate,
    ScheduleItemRead,
    ScheduleItemUpdate,
)


class TestScheduleItem:
    def test_db_model(self, user: User, task: Task, session: Session) -> None:
        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + dt.timedelta(hours=2)

        schedule_item_data = {
            "user_id": user.id,  # type: ignore[attr-defined]
            "task_id": task.id,  # type: ignore[attr-defined]
            "start_time": start_time,
            "end_time": end_time,
            "source": "task",
            "title": "Scheduled Task Item",
        }

        schedule_item = ScheduleItem.model_validate(schedule_item_data)
        assert schedule_item.user_id == user.id  # type: ignore[attr-defined]
        assert schedule_item.task_id == task.id  # type: ignore[attr-defined]
        assert schedule_item.id is None
        session.add(schedule_item)
        session.commit()
        session.refresh(schedule_item)
        assert schedule_item.id is not None

    def test_no_task(self, user: User, session: Session) -> None:
        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + dt.timedelta(hours=2)

        schedule_item_data = {
            "user_id": user.id,  # type: ignore[attr-defined]
            "start_time": start_time,
            "end_time": end_time,
            "source": "other",
            "title": "Scheduled Item from other source",
        }

        scheduled_item = ScheduleItem.model_validate(schedule_item_data)
        assert scheduled_item.user_id == user.id  # type: ignore[attr-defined]
        assert scheduled_item.task_id is None
        session.add(scheduled_item)
        session.commit()
        session.refresh(scheduled_item)
        assert scheduled_item.id is not None
        assert scheduled_item.source == "other"
        assert scheduled_item.task_id is None

    def test_create(self, task: Task, user: User) -> None:
        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + dt.timedelta(hours=2)

        scheduled_item = ScheduleItemCreate(
            user_id=user.id,  # type: ignore[attr-defined]
            task_id=task.id,  # type: ignore[attr-defined]
            start_time=start_time,
            end_time=end_time,
            title="Create Schedule Item",
        )

        assert scheduled_item.start_time is not None
        assert scheduled_item.title == "Create Schedule Item"
        assert scheduled_item.source == "task"

    def test_update(self, session: Session, schedule_item: ScheduleItem) -> None:
        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + dt.timedelta(hours=2)
        schedule_start_time = (
            schedule_item.start_time.replace(tzinfo=dt.timezone.utc)  # type: ignore[attr-defined]
            if schedule_item.start_time.tzinfo is None  # type: ignore[attr-defined]
            else schedule_item.start_time  # type: ignore[attr-defined]
        )
        assert schedule_start_time != start_time

        schedule_update_item = ScheduleItemUpdate(
            start_time=start_time,
            end_time=end_time,
        )
        update_data = schedule_update_item.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(schedule_item, field, value)

        session.add(schedule_item)
        session.commit()
        session.refresh(schedule_item)
        schedule_start_time = (
            schedule_item.start_time.replace(tzinfo=dt.timezone.utc)  # type: ignore[attr-defined]
            if schedule_item.start_time.tzinfo is None  # type: ignore[attr-defined]
            else schedule_item.start_time  # type: ignore[attr-defined]
        )
        assert schedule_start_time == start_time

    def test_read(self, session: Session, schedule_item: ScheduleItem) -> None:
        schedule_item_read = ScheduleItemRead.model_validate(schedule_item)

        assert schedule_item_read.id == schedule_item.id  # type: ignore[attr-defined]
        assert schedule_item_read.user_id == schedule_item.user_id  # type: ignore[attr-defined]
        assert schedule_item_read.task_id == schedule_item.task_id  # type: ignore[attr-defined]
        assert schedule_item_read.start_time == schedule_item.start_time  # type: ignore[attr-defined]
        assert schedule_item_read.end_time == schedule_item.end_time  # type: ignore[attr-defined]
        assert schedule_item_read.title == schedule_item.title  # type: ignore[attr-defined]
        assert schedule_item_read.description == schedule_item.description  # type: ignore[attr-defined]
        assert schedule_item_read.source == schedule_item.source  # type: ignore[attr-defined]
        assert schedule_item_read.created_at == schedule_item.created_at  # type: ignore[attr-defined]
        assert schedule_item_read.updated_at == schedule_item.updated_at  # type: ignore[attr-defined]

        json_data = schedule_item_read.model_dump()
        assert "id" in json_data
        assert "user_id" in json_data
        assert "task_id" in json_data
        assert "start_time" in json_data
        assert "end_time" in json_data
        assert "title" in json_data
        assert "description" in json_data
        assert "source" in json_data

        read_from_dict = ScheduleItemRead.model_validate(json_data)
        assert read_from_dict.id == schedule_item.id  # type: ignore[attr-defined]
        assert read_from_dict.user_id == schedule_item.user_id  # type: ignore[attr-defined]

    def test_create_past_datetime(self, task: Task) -> None:
        tomorrow = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=-5)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + dt.timedelta(hours=2)

        with pytest.raises(ValueError, match="Schedule times must be in the future"):
            ScheduleItemCreate(
                task_id=task.id,  # type: ignore[attr-defined]
                start_time=start_time,
                end_time=end_time,
                title="Create Schedule Item",
            )

    def test_update_past_datetime(self) -> None:
        yesterday = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=-5)
        start_time = yesterday.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + dt.timedelta(hours=2)
        with pytest.raises(ValueError, match="Schedule times must be in the future"):
            ScheduleItemUpdate(
                start_time=start_time,
                end_time=end_time,
            )

    def test_update_end_before_start(self) -> None:
        yesterday = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=5)
        start_time = yesterday.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + dt.timedelta(hours=-2)
        with pytest.raises(ValueError, match="End time must be after start time"):
            ScheduleItemUpdate(
                start_time=start_time,
                end_time=end_time,
            )
