from sqlmodel import Field, SQLModel


class UserSetting(SQLModel, table=True):
    __tablename__ = "user_settings"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    key: str = Field(index=True)  # e.g., "timezone", "notification_pref"
    value: str  # The value, e.g., "America/Los_Angeles"
