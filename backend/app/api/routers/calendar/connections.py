from fastapi import APIRouter, Depends
from sqlmodel import Session

import app.crud.calendar_connection_crud as calendar_connection_crud
from app.core.auth import get_current_user_id
from app.core.db import get_db
from app.schemas.calendar_connections import CalendarConnectionCreate

router: APIRouter = APIRouter(prefix="/connections", tags=["connections"])


@router.post("/")
async def add_calendar_connection(
    calendar_connection: CalendarConnectionCreate,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
):
    """Add a calendar connection for the user."""
    return calendar_connection_crud.create_calendar_connection(
        calendar_connection=calendar_connection, user_id=user_id, session=session
    )
