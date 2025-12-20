from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    try:
        payload: dict[str, Any] = decode_access_token(token)
        user_id: int | None = payload["sub"]
        if user_id is None:
            raise ValueError("User ID is required")
        user = session.get(User, user_id)
        if user is None:
            raise ValueError("User not found")
        return user
    except ValueError:
        raise ValueError("Invalid token")

def get_current_user_id(current_user: User = Depends(get_current_user)) -> int:
    if current_user.id is None:
        raise ValueError("User ID is required")
    return current_user.id
