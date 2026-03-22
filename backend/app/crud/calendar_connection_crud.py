from sqlmodel import Session, select

from app.core.timezone import now_utc
from app.models.calender_connections import CalendarConnection
from app.schemas.calendar_connections import CalendarConnectionCreate


def create_calendar_connection(
    calendar_connection: CalendarConnectionCreate, user_id: int, session: Session
) -> CalendarConnection:
    calendar_connection_model: CalendarConnection = CalendarConnection(
        **calendar_connection.model_dump(),
        user_id=user_id,
        secret_updated_at=now_utc() if calendar_connection.secret else None,
    )
    calendar_connection_model.user_id = user_id
    session.add(calendar_connection_model)
    session.flush()
    session.refresh(calendar_connection_model)
    return calendar_connection_model


def get_calendar_connections_by_user_id(
    user_id: int, session: Session
) -> list[CalendarConnection]:
    return list(
        session.exec(
            select(CalendarConnection).where(CalendarConnection.user_id == user_id)
        ).all()
    )
