
from sqlmodel import Session

from app.schemas.calendar_connections import CalendarConnectionCreate
from app.models.calender_connections import CalendarConnection

def create_calendar_connection(
    calendar_connection: CalendarConnectionCreate, user_id: int, session: Session
) -> CalendarConnection:
    calendar_connection_model: CalendarConnection = CalendarConnection.model_validate(calendar_connection)
    calendar_connection_model.user_id = user_id
    session.add(calendar_connection_model)
    session.flush()
    session.refresh(calendar_connection_model)
    return calendar_connection_model