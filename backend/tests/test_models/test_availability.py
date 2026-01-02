import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.availability import DailyWindowModel, WeeklyAvailability
from app.models.user import User
from app.schemas.availability import (
    DailyWindow as DailyWindowSchema,
)
from app.schemas.availability import (
    DayOfWeek,
    WeeklyAvailabilityCreate,
    WeeklyAvailabilityRead,
)
from app.services.scheduling_types import SchedulerAvailability


class TestWeeklyAvailability:
    def test_db_model(self, user: User, session: Session) -> None:
        availability_data = {
            "user_id": user.id,  # type: ignore[attr-defined]
        }

        availability = WeeklyAvailability.model_validate(availability_data)
        session.add(availability)
        session.commit()
        session.refresh(availability)

        assert availability.id is not None
        assert availability.user_id == user.id

    def test_create(self) -> None:
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

        assert availability_create.windows is not None
        assert len(availability_create.windows) == 2
        assert DayOfWeek.MON in availability_create.windows
        assert availability_create.windows[DayOfWeek.MON] is not None
        assert len(availability_create.windows[DayOfWeek.MON]) == 2

    def test_update(
        self, session: Session, weekly_availability: WeeklyAvailability
    ) -> None:
        # Clear existing windows
        from sqlmodel import select

        windows_to_delete = list(
            session.exec(
                select(DailyWindowModel).where(
                    DailyWindowModel.weekly_availability_id
                    == weekly_availability.id
                )
            ).all()
        )
        for window in windows_to_delete:
            session.delete(window)
        session.commit()

        # Add new window
        new_window = DailyWindowModel(
            weekly_availability_id=weekly_availability.id,  # type: ignore[attr-defined]
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

    def test_read(
        self,
        session: Session,
        weekly_availability: WeeklyAvailability,
        daily_windows: None,
    ) -> None:
        # Test converting SQLModel to Pydantic Read DTO
        session.refresh(weekly_availability)
        availability_read = WeeklyAvailabilityRead.model_validate(weekly_availability)

        # Verify all fields are properly mapped
        assert availability_read.id == weekly_availability.id
        assert availability_read.user_id == weekly_availability.user_id  # type: ignore[attr-defined]
        assert availability_read.created_at == weekly_availability.created_at  # type: ignore[attr-defined]
        assert availability_read.updated_at == weekly_availability.updated_at  # type: ignore[attr-defined]

        # Test that the Read DTO can be serialized to JSON
        json_data = availability_read.model_dump()
        assert "id" in json_data
        assert "user_id" in json_data
        assert "windows" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

        # Test creating Read DTO from dict (simulating API response)
        read_from_dict = WeeklyAvailabilityRead.model_validate(json_data)
        assert read_from_dict.id == weekly_availability.id  # type: ignore[attr-defined]
        assert read_from_dict.user_id == weekly_availability.user_id  # type: ignore[attr-defined]
        assert read_from_dict.created_at == weekly_availability.created_at  # type: ignore[attr-defined]
        assert read_from_dict.updated_at == weekly_availability.updated_at  # type: ignore[attr-defined]

    def test_read_with_daily_windows(
        self,
        session: Session,
        weekly_availability: WeeklyAvailability,
        daily_windows: None,
    ) -> None:
        """
        Test that DailyWindow models are properly converted to the Pydantic schema format.
        """
        session.refresh(weekly_availability)

        availability_read = WeeklyAvailabilityRead.model_validate(weekly_availability)

        assert availability_read.windows is not None

        for day_int in range(7):
            day = DayOfWeek(day_int)
            assert day in availability_read.windows
            assert availability_read.windows[day] is not None
            assert len(availability_read.windows[day]) == 2

            first_window = availability_read.windows[day][0]
            assert first_window.start == dt.time(7, 0)
            assert first_window.end == dt.time(12, 0)

            second_window = availability_read.windows[day][1]
            assert second_window.start == dt.time(13, 0)
            assert second_window.end == dt.time(17, 0)

    def test_default_windows(self) -> None:
        availability_create = WeeklyAvailabilityCreate()
        assert availability_create.windows == {}

    def test_model_validator_scheduler_availability(
        self,
        session: Session,
        weekly_availability: WeeklyAvailability,
        daily_windows: None,
    ) -> None:
        session.refresh(weekly_availability)
        scheduler_availability = SchedulerAvailability.model_validate(
            weekly_availability
        )

        assert scheduler_availability.windows is not None

        for day_int in range(7):
            day = DayOfWeek(day_int)
            assert day in scheduler_availability.windows
            assert scheduler_availability.windows[day] is not None
            assert len(scheduler_availability.windows[day]) == 2  # 2 windows per day

            first_window = scheduler_availability.windows[day][0]
            assert first_window.start == dt.time(7, 0)
            assert first_window.end == dt.time(12, 0)

            second_window = scheduler_availability.windows[day][1]
            assert second_window.start == dt.time(13, 0)
            assert second_window.end == dt.time(17, 0)


class TestDailyWindow:
    def test_db_model(
        self, weekly_availability: WeeklyAvailability, session: Session
    ) -> None:
        window_data = {
            "weekly_availability_id": weekly_availability.id,  # type: ignore[attr-defined]
            "day_of_week": 1,  # Tuesday
            "start_time": dt.time(9, 0),
            "end_time": dt.time(17, 0),
        }

        window = DailyWindowModel.model_validate(window_data)
        session.add(window)
        session.commit()
        session.refresh(window)

        assert window.id is not None
        assert window.weekly_availability_id == weekly_availability.id  # type: ignore[attr-defined]
        assert window.day_of_week == 1
        assert window.start_time == dt.time(9, 0)
        assert window.end_time == dt.time(17, 0)

    def test_schema(self) -> None:
        window_schema = DailyWindowSchema(start=dt.time(10, 30), end=dt.time(16, 45))

        assert window_schema.start == dt.time(10, 30)
        assert window_schema.end == dt.time(16, 45)

    def test_day_of_week_enum(self) -> None:
        assert DayOfWeek.MON == 0
        assert DayOfWeek.TUE == 1
        assert DayOfWeek.WED == 2
        assert DayOfWeek.THU == 3
        assert DayOfWeek.FRI == 4
        assert DayOfWeek.SAT == 5
        assert DayOfWeek.SUN == 6

    def test_unique_constraint(
        self, weekly_availability: WeeklyAvailability, session: Session
    ) -> None:
        window1 = DailyWindowModel(
            weekly_availability_id=weekly_availability.id,  # type: ignore[attr-defined]
            day_of_week=1,
            start_time=dt.time(9, 0),
            end_time=dt.time(12, 0),
        )
        session.add(window1)
        session.commit()

        window2 = DailyWindowModel(
            weekly_availability_id=weekly_availability.id,  # type: ignore[attr-defined]
            day_of_week=1,
            start_time=dt.time(9, 0),  # Same start time
            end_time=dt.time(17, 0),
        )
        session.add(window2)

        with pytest.raises(IntegrityError):  # SQLAlchemy IntegrityError
            session.commit()

        session.rollback()

        window3 = DailyWindowModel(
            weekly_availability_id=weekly_availability.id,  # type: ignore[attr-defined]
            day_of_week=1,
            start_time=dt.time(13, 0),
            end_time=dt.time(17, 0),
        )
        session.add(window3)
        session.commit()
