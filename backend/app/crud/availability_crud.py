from sqlmodel import Session, select

from app.models.availability import WeeklyAvailability


def get_user_availability(user_id: int, session: Session) -> WeeklyAvailability:
    return session.exec(
        select(WeeklyAvailability).where(WeeklyAvailability.user_id == user_id)
    ).one()
