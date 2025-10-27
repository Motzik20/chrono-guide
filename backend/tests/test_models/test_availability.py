import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.availability import DailyWindow, WeeklyAvailability
from app.schemas.availability import (
    DailyWindow as DailyWindowSchema,
)
from app.schemas.availability import (
    DayOfWeek,
    WeeklyAvailabilityCreate,
    WeeklyAvailabilityRead,
)
from app.services.scheduling_service import SchedulerAvailability


class TestWeeklyAvailability:
    def test_db_model(self, user, session):
        availability_data = {
            "user_id": user.id,
        }

        availability = WeeklyAvailability.model_validate(availability_data)
        session.add(availability)
        session.commit()
        session.refresh(availability)

        assert availability.id is not None
        assert availability.user_id == user.id

    def test_create(self):
        availability_create = WeeklyAvailabilityCreate(
            windows={
                DayOfWeek.MON: [
                    DailyWindowSchema(start=dt.time(9, 0), end=dt.time(12, 0)),
                    DailyWindowSchema(start=dt.time(13, 0), end=dt.time(17, 0)),
                ],
                DayOfWeek.TUE: [
                    DailyWindowSchema(start=dt.time(9, 0), end=dt.time(17, 0))
                ],
            },
        )

        assert len(availability_create.windows) == 2
        assert DayOfWeek.MON in availability_create.windows
        assert len(availability_create.windows[DayOfWeek.MON]) == 2

    def test_update(self, session, weekly_availability):
        # Clear existing windows
        from sqlmodel import select

        windows_to_delete = session.exec(
            select(DailyWindow).where(
                DailyWindow.weekly_availability_id == weekly_availability.id
            )
        ).all()
        for window in windows_to_delete:
            session.delete(window)
        session.commit()

        # Add new window
        new_window = DailyWindow(
            weekly_availability_id=weekly_availability.id,
            day_of_week=DayOfWeek.WED,
            start_time=dt.time(10, 0),
            end_time=dt.time(18, 0),
        )
        session.add(new_window)
        session.commit()
        session.refresh(weekly_availability)

        # Test that windows were updated
        assert len(weekly_availability.windows) == 1
        assert weekly_availability.windows[0].day_of_week == DayOfWeek.WED

    def test_read(self, session, weekly_availability, daily_windows):
        # Test converting SQLModel to Pydantic Read DTO
        session.refresh(weekly_availability)
        availability_read = WeeklyAvailabilityRead.model_validate(weekly_availability)

        # Verify all fields are properly mapped
        assert availability_read.id == weekly_availability.id
        assert availability_read.user_id == weekly_availability.user_id
        assert availability_read.created_at == weekly_availability.created_at
        assert availability_read.updated_at == weekly_availability.updated_at

        # Test that the Read DTO can be serialized to JSON
        json_data = availability_read.model_dump()
        assert "id" in json_data
        assert "user_id" in json_data
        assert "windows" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

        # Test creating Read DTO from dict (simulating API response)
        read_from_dict = WeeklyAvailabilityRead.model_validate(json_data)
        assert read_from_dict.id == weekly_availability.id
        assert read_from_dict.user_id == weekly_availability.user_id
        assert read_from_dict.created_at == weekly_availability.created_at
        assert read_from_dict.updated_at == weekly_availability.updated_at

    def test_read_with_daily_windows(self, session, weekly_availability, daily_windows):
        """
        Test that DailyWindow models are properly converted to the Pydantic schema format.
        """
        session.refresh(weekly_availability)

        availability_read = WeeklyAvailabilityRead.model_validate(weekly_availability)

        assert availability_read.windows is not None

        for day in range(7):
            assert day in availability_read.windows
            assert len(availability_read.windows[day]) == 2

            first_window = availability_read.windows[day][0]
            assert first_window.start == dt.time(7, 0)
            assert first_window.end == dt.time(12, 0)

            second_window = availability_read.windows[day][1]
            assert second_window.start == dt.time(13, 0)
            assert second_window.end == dt.time(17, 0)

    def test_default_windows(self):
        availability_create = WeeklyAvailabilityCreate()
        assert availability_create.windows == {}

    def test_model_validator_non_dict_data(self):
        """Test that the model validator handles non-dict data correctly."""
        result = WeeklyAvailability.convert_datetimes_to_utc(None)
        assert result is None

        result = WeeklyAvailability.convert_datetimes_to_utc("not a dict")
        assert result == "not a dict"

    def test_model_validator_scheduler_availability(
        self, session, weekly_availability, daily_windows
    ):
        session.refresh(weekly_availability)
        scheduler_availability = SchedulerAvailability.model_validate(
            weekly_availability
        )

        assert scheduler_availability.windows is not None

        for day in range(7):
            assert day in scheduler_availability.windows
            assert len(scheduler_availability.windows[day]) == 2  # 2 windows per day

            first_window = scheduler_availability.windows[day][0]
            assert first_window.start == dt.time(7, 0)
            assert first_window.end == dt.time(12, 0)

            second_window = scheduler_availability.windows[day][1]
            assert second_window.start == dt.time(13, 0)
            assert second_window.end == dt.time(17, 0)


class TestDailyWindow:
    def test_db_model(self, weekly_availability, session):
        window_data = {
            "weekly_availability_id": weekly_availability.id,
            "day_of_week": 1,  # Tuesday
            "start_time": dt.time(9, 0),
            "end_time": dt.time(17, 0),
        }

        window = DailyWindow.model_validate(window_data)
        session.add(window)
        session.commit()
        session.refresh(window)

        assert window.id is not None
        assert window.weekly_availability_id == weekly_availability.id
        assert window.day_of_week == 1
        assert window.start_time == dt.time(9, 0)
        assert window.end_time == dt.time(17, 0)

    def test_schema(self):
        window_schema = DailyWindowSchema(start=dt.time(10, 30), end=dt.time(16, 45))

        assert window_schema.start == dt.time(10, 30)
        assert window_schema.end == dt.time(16, 45)

    def test_day_of_week_enum(self):
        assert DayOfWeek.MON == 0
        assert DayOfWeek.TUE == 1
        assert DayOfWeek.WED == 2
        assert DayOfWeek.THU == 3
        assert DayOfWeek.FRI == 4
        assert DayOfWeek.SAT == 5
        assert DayOfWeek.SUN == 6

    def test_unique_constraint(self, weekly_availability, session):
        window1 = DailyWindow(
            weekly_availability_id=weekly_availability.id,
            day_of_week=1,
            start_time=dt.time(9, 0),
            end_time=dt.time(12, 0),
        )
        session.add(window1)
        session.commit()

        window2 = DailyWindow(
            weekly_availability_id=weekly_availability.id,
            day_of_week=1,
            start_time=dt.time(9, 0),  # Same start time
            end_time=dt.time(17, 0),
        )
        session.add(window2)

        with pytest.raises(IntegrityError):  # SQLAlchemy IntegrityError
            session.commit()

        session.rollback()

        window3 = DailyWindow(
            weekly_availability_id=weekly_availability.id,
            day_of_week=1,
            start_time=dt.time(13, 0),
            end_time=dt.time(17, 0),
        )
        session.add(window3)
        session.commit()

    def test_model_validator_non_dict_data(self):
        """Test that the model validator handles non-dict data correctly."""
        result = DailyWindow.convert_datetimes_to_utc(None)
        assert result is None

        result = DailyWindow.convert_datetimes_to_utc("not a dict")
        assert result == "not a dict"
