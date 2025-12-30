from fastapi import APIRouter, Body, Depends
from sqlmodel import Session

from app.core.auth import get_current_user_id
from app.core.db import get_db
from app.schemas.availability import WeeklyAvailabilityUpdate
from app.schemas.user import AnySettingOut, SettingUpdate
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
async def get_settings(
    user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)
):
    """Get all user settings including availability."""
    return settings_service.get_all_user_settings(user_id, session)


@router.get("/options/{key}")
async def get_options(
    key: str,
    user_id: int = Depends(get_current_user_id),  # noqa: ARG001
) -> list[dict[str, str]] | None:
    """Get options for a specific setting key."""
    return settings_service.get_setting_options(key)


@router.patch("/")
async def update_settings(
    setting: SettingUpdate = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> AnySettingOut:
    """Update a user setting."""
    if setting.type == "schedule":
        availability_update = WeeklyAvailabilityUpdate.model_validate(
            {"windows": setting.value}
        )
        return settings_service.update_availability_setting(
            user_id, availability_update, session
        )
    return settings_service.update_setting(user_id, setting, session)
