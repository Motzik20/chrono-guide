from fastapi import APIRouter, Body, Depends
from fastapi.responses import Response
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.crud import user_crud
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/registration")
async def get_registration(
    user: UserCreate = Body(...), session: Session = Depends(get_db)
) -> User:
    return user_crud.create_user(user, session)


@router.post("/login")
async def login(
    user: UserLogin = Body(...), session: Session = Depends(get_db)
) -> Response:
    response = Response()
    response.set_cookie(
        key="access_token",
        value=user_crud.login(user, session)["access_token"],
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout() -> Response:
    response = Response()
    response.delete_cookie(key="access_token")
    return response


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """Get the current authenticated user's info. Used to verify authentication."""
    return UserOut.model_validate(current_user)
