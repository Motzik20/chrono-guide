import datetime as dt

from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models.availability import DailyWindowModel, WeeklyAvailability
from app.schemas.availability import DayOfWeek, WeeklyAvailabilityUpdate


def get_user_availability(user_id: int, session: Session) -> WeeklyAvailability:
    """Get user availability from the database."""
    availability = session.exec(
        select(WeeklyAvailability).where(WeeklyAvailability.user_id == user_id)
    ).one_or_none()
    if not availability:
        raise NotFoundError("No availability found for user")
    return availability


def create_user_availability(user_id: int, session: Session) -> WeeklyAvailability:
    """Create default availability for a user."""
    availability = WeeklyAvailability(user_id=user_id)
    session.add(availability)
    session.flush()
    session.refresh(availability)
    assert availability.id is not None
    for day_of_week in DayOfWeek:
        session.add(
            DailyWindowModel(
                weekly_availability_id=availability.id,
                day_of_week=day_of_week,
                start_time=dt.time(7, 0),
                end_time=dt.time(17, 0),
            )
        )
    session.flush()
    session.refresh(availability)
    return availability


def update_user_availability(
    user_id: int, availability: WeeklyAvailabilityUpdate, session: Session
) -> WeeklyAvailability:
    """Update user availability in the database. Returns the updated model."""
    db_availability: WeeklyAvailability = get_user_availability(user_id, session)
    assert db_availability.id is not None

    # Delete existing windows
    for window in db_availability.windows:
        session.delete(window)

    # Create new windows
    for day_of_week, windows in availability.windows.items():
        for window in windows:
            daily_window = DailyWindowModel(
                weekly_availability_id=db_availability.id,
                day_of_week=DayOfWeek(day_of_week),
                start_time=window.start,
                end_time=window.end,
            )
            session.add(daily_window)

    session.flush()
    session.refresh(db_availability)
    return db_availability
