import datetime as dt
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from app.core.default_settings import METADATA_SETTINGS
from app.schemas.availability import DailyWindow, DayOfWeek


class UserBase(BaseModel):
    @field_validator("email", check_fields=False)
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if "@" not in v:
            raise ValueError("Email must contain @")
        return v.lower()


class UserCreate(UserBase):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(UserBase):
    email: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


# ==== Settings Schemas ====


class SettingBaseOut(BaseModel):
    id: int | None = None
    key: str
    label: str | None = None
    description: str
    option_type: str | None = None


class StringSettingOut(SettingBaseOut):
    type: Literal["string"] = "string"
    value: str


class BooleanSettingOut(SettingBaseOut):
    type: Literal["boolean"] = "boolean"
    value: str


class ScheduleSettingOut(SettingBaseOut):
    type: Literal["schedule"] = "schedule"
    value: dict[DayOfWeek, list[DailyWindow]]


AnySettingOut = Annotated[
    StringSettingOut | BooleanSettingOut | ScheduleSettingOut,
    Field(discriminator="type"),
]


class UserSettingsOut(BaseModel):
    settings: list[AnySettingOut]


class SettingUpdateBase(BaseModel):
    key: str
    label: str | None = None

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        if v not in METADATA_SETTINGS.keys():
            raise ValueError(f"Invalid key: {v}")
        return v


class StringSettingUpdate(SettingUpdateBase):
    value: str
    type: Literal["string"] = "string"


class BooleanSettingUpdate(SettingUpdateBase):
    value: str
    type: Literal["boolean"] = "boolean"


class ScheduleSettingUpdate(SettingUpdateBase):
    value: dict[DayOfWeek, list[DailyWindow]]
    type: Literal["schedule"] = "schedule"


SettingUpdate = Annotated[
    StringSettingUpdate | BooleanSettingUpdate | ScheduleSettingUpdate,
    Field(discriminator="type"),
]
