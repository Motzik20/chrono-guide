from fastapi import APIRouter, Body, Depends
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.crud import setting_crud
from app.schemas.user import UserSettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
async def get_settings(
    user_id: int = Depends(get_current_user), session: Session = Depends(get_db)
):
    return setting_crud.get_user_settings(user_id, session)


@router.patch("/")
async def update_settings(
    setting: UserSettingUpdate = Body(...),
    user_id: int = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return setting_crud.update_user_setting(user_id, setting, session)
