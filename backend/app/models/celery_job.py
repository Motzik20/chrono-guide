import datetime as dt

from sqlmodel import Field, SQLModel

from app.core.timezone import now_utc


class CeleryJob(SQLModel, table=True):
    __tablename__ = "celery_jobs"  # type: ignore[assignment]

    id: str = Field(primary_key=True)
    task_name: str = Field(index=True)
    user_id: int = Field(index=True)
    created_at: dt.datetime = Field(default_factory=now_utc)
