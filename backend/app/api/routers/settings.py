from fastapi import APIRouter, Body, Depends
from sqlmodel import Session

from app.core.auth import get_current_user_id
from app.core.db import get_db
from app.core.default_settings import METADATA_SETTINGS
from app.core.exceptions import NotFoundError
from app.crud import availability_crud, setting_crud
from app.schemas.availability import WeeklyAvailabilityUpdate
from app.schemas.user import AnySettingOut, SettingUpdate
from app.services.option_factory_service import OPTION_FACTORIES

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
async def get_settings(
    user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)
):
    return setting_crud.get_user_settings(user_id, session)


@router.get("/options/{key}")
async def get_options(
    key: str,
    user_id: int = Depends(get_current_user_id),
) -> list[dict[str, str]] | None:
    assert user_id is not None
    metadata = METADATA_SETTINGS.get(key)
    if not metadata:
        raise NotFoundError(f"No metadata found for setting key: {key}")
    if "options" in metadata and metadata.get("option_type") == "static":
        options = metadata.get("options")
        if not isinstance(options, list):
            return None
        return options

    if metadata.get("option_type") == "dynamic":
        factory_function = metadata.get("options")
        if not isinstance(factory_function, str):
            return None

        factory_func = OPTION_FACTORIES.get(factory_function)
        if not factory_func:
            return None
        return factory_func()
    return None


@router.patch("/")
async def update_settings(
    setting: SettingUpdate = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> AnySettingOut:
    if setting.type == "schedule":
        availability = availability_crud.update_user_availability(
            user_id,
            WeeklyAvailabilityUpdate.model_validate({"windows": setting.value}),
            session,
        )
        return availability
    return setting_crud.update_user_setting(user_id, setting, session)
