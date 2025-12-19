from fastapi import APIRouter, Body, Depends
from sqlmodel import Session

from app.core.db import get_db
from app.crud import user_crud
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/registration")
async def get_registration(user: UserCreate = Body(...), session: Session = Depends(get_db)) -> User:
    return user_crud.create_user(user, session)

@router.post("/login")
async def login(user: UserLogin = Body(...), session: Session = Depends(get_db)) -> User:
    return user_crud.login(user, session)
