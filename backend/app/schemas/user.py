import datetime as dt

from pydantic import BaseModel, Field, field_validator


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
