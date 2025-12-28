from sqlmodel import Field, SQLModel


class UserSetting(SQLModel, table=True):
    __tablename__ = "user_settings"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    key: str = Field(index=True)
    value: str
    label: str | None = Field(default=None)
