from typing import Any

from fastapi import Cookie, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User


def get_current_user(
    access_token: str | None = Cookie(None, alias="access_token"),
    session: Session = Depends(get_db),
) -> User:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload: dict[str, Any] = decode_access_token(access_token)
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid access token")
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid access token")
        return user
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token")


def get_current_user_id(current_user: User = Depends(get_current_user)) -> int:
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return current_user.id
