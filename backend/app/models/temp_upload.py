from sqlalchemy import Column, LargeBinary, String
from sqlmodel import Field, SQLModel


class TempUpload(SQLModel, table=True):
    __tablename__ = "temp_uploads"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    filename: str | None = Field(default=None, sa_column=Column(String, nullable=False))
    data: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
