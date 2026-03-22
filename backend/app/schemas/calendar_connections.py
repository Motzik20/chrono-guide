from pydantic import BaseModel


class CalendarConnectionCreate(BaseModel):
    connection_type: str
    label: str
    calendar_url: str
    username: str | None = None
    key_id: str | None = None
    secret: str | None = None
