import datetime as dt

import pytest

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate


class TestTask:
    def test_db_model(self, session, user):
        task_data = {
            "user_id": user.id,
            "title": "Test Data Task",
            "description": "A direct pydantic data Task conversion",
            "expected_duration_minutes": 60,
            "priority": 1,
        }

        task = Task.model_validate(task_data)
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.id is not None
        assert task.title == "Test Data Task"
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.priority == 1

    def test_create(self, task):
        task_create = TaskCreate(
            title="New Task",
            description="A new task for testing",
            expected_duration_minutes=90,
            priority=2,
            tips=["tip1", "tip2"],
        )

        assert task_create.title == "New Task"
        assert task_create.description == "A new task for testing"
        assert task_create.expected_duration_minutes == 90
        assert task_create.priority == 2
        assert task_create.tips == ["tip1", "tip2"]

    def test_update(self, session, task):
        original_title = task.title

        task_update = TaskUpdate(title="Updated Task Title", priority=0)

        update_data = task_update.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.title == "Updated Task Title"
        assert task.title != original_title
        assert task.priority == 0

    def test_read(self, session, task):
        task_read = TaskRead.model_validate(task)

        assert task_read.id == task.id
        assert task_read.user_id == task.user_id
        assert task_read.title == task.title
        assert task_read.description == task.description
        assert task_read.expected_duration_minutes == task.expected_duration_minutes
        assert task_read.priority == task.priority

        expected_tips = task.tips if task.tips is not None else []
        assert task_read.tips == expected_tips
        assert task_read.created_at == task.created_at
        assert task_read.updated_at == task.updated_at

        json_data = task_read.model_dump()
        assert "id" in json_data
        assert "user_id" in json_data
        assert "title" in json_data
        assert "description" in json_data
        assert "expected_duration_minutes" in json_data
        assert "priority" in json_data
        assert "tips" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

        read_from_dict = TaskRead.model_validate(json_data)
        assert read_from_dict.id == task.id
        assert read_from_dict.title == task.title

    def test_create_empty_title(self):
        with pytest.raises(ValueError):
            TaskCreate(
                title=None,
                description="Valid description",
                expected_duration_minutes=60,
            )

    def test_create_empty_description(self):
        with pytest.raises(ValueError):
            TaskCreate(
                title="Valid title", description=None, expected_duration_minutes=60
            )

    def test_create_invalid_duration(self):
        with pytest.raises(ValueError):
            TaskCreate(
                title="Valid title",
                description="Valid description",
                expected_duration_minutes=0,
            )

    def test_create_invalid_priority(self):
        with pytest.raises(ValueError):
            TaskCreate(
                title="Valid title",
                description="Valid description",
                expected_duration_minutes=60,
                priority=5,  # Should be 0-4
            )

    def test_create_past_deadline(self):
        past_time = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)

        with pytest.raises(ValueError, match="Deadline must be in the future"):
            TaskCreate(
                title="Valid title",
                description="Valid description",
                expected_duration_minutes=60,
                deadline=past_time,
            )

    def test_create_far_future_deadline(self):
        far_future = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            days=365 * 11
        )  # 11 years

        with pytest.raises(ValueError, match="Deadline cannot be more than 10 years"):
            TaskCreate(
                title="Valid title",
                description="Valid description",
                expected_duration_minutes=60,
                deadline=far_future,
            )

    def test_create_valid_deadline(self):
        future_time = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)

        task_create = TaskCreate(
            title="Valid title",
            description="Valid description",
            expected_duration_minutes=60,
            deadline=future_time,
        )

        assert task_create.deadline == future_time

    def test_defaults(self):
        task_create = TaskCreate(
            title="Title", description="Description", expected_duration_minutes=30
        )

        assert task_create.priority == 2
        assert task_create.tips == []
        assert task_create.deadline is None

    def test_read_with_none_tips(self, session, user):
        task_data = {
            "user_id": user.id,
            "title": "Task with None tips",
            "description": "Testing None tips handling",
            "expected_duration_minutes": 30,
            "tips": None,  # Explicitly set to None
        }

        task = Task.model_validate(task_data)
        session.add(task)
        session.commit()
        session.refresh(task)

        task_read = TaskRead.model_validate(task)
        assert task_read.tips == []

    def test_model_validator_naive_deadline(self, session, user):
        """Test that naive datetime objects are converted to UTC by the model validator."""
        naive_deadline = dt.datetime(2025, 12, 25, 14, 30, 0)  # No timezone

        task_data = {
            "user_id": user.id,
            "title": "Task with naive deadline",
            "description": "Testing naive datetime conversion",
            "expected_duration_minutes": 60,
            "deadline": naive_deadline,
        }

        task = Task.model_validate(task_data)

        assert task.deadline is not None
        assert task.deadline.tzinfo == dt.timezone.utc
        assert task.deadline.year == 2025
        assert task.deadline.month == 12
        assert task.deadline.day == 25
        assert task.deadline.hour == 14
        assert task.deadline.minute == 30

    def test_model_validator_naive_created_at(self, session, user):
        """Test that naive datetime objects in created_at are converted to UTC."""
        # Create a naive datetime for created_at
        naive_created_at = dt.datetime(2025, 1, 1, 10, 0, 0)  # No timezone

        task_data = {
            "user_id": user.id,
            "title": "Task with naive created_at",
            "description": "Testing naive datetime conversion",
            "expected_duration_minutes": 60,
            "created_at": naive_created_at,
        }

        task = Task.model_validate(task_data)

        assert task.created_at is not None
        assert task.created_at.tzinfo == dt.timezone.utc
        assert task.created_at.year == 2025
        assert task.created_at.month == 1
        assert task.created_at.day == 1
        assert task.created_at.hour == 10
        assert task.created_at.minute == 0

    def test_model_validator_aware_datetime_preserved(self, session, user):
        """Test that timezone-aware datetime objects are preserved by the model validator."""
        # Create a timezone-aware datetime
        aware_deadline = dt.datetime(2025, 12, 25, 14, 30, 0, tzinfo=dt.timezone.utc)

        task_data = {
            "user_id": user.id,
            "title": "Task with aware deadline",
            "description": "Testing aware datetime preservation",
            "expected_duration_minutes": 60,
            "deadline": aware_deadline,
        }

        task = Task.model_validate(task_data)

        assert task.deadline is not None
        assert task.deadline.tzinfo == dt.timezone.utc
        assert task.deadline == aware_deadline

    def test_model_validator_no_datetime_fields(self, session, user):
        """Test that the model validator works when no datetime fields are provided."""
        task_data = {
            "user_id": user.id,
            "title": "Task without datetime fields",
            "description": "Testing model validator with no datetimes",
            "expected_duration_minutes": 60,
        }

        task = Task.model_validate(task_data)

        assert task.title == "Task without datetime fields"
        assert task.deadline is None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_model_validator_non_dict_data(self):
        """Test that the model validator handles non-dict data correctly."""
        result = Task.convert_datetimes_to_utc(None)
        assert result is None

        result = Task.convert_datetimes_to_utc("not a dict")
        assert result == "not a dict"

        result = Task.convert_datetimes_to_utc({"title": "test", "description": "test"})
        assert isinstance(result, dict)
        assert result["title"] == "test"
