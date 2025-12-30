from typing import Any

from sqlmodel import Session, select

from app.core.default_settings import METADATA_SETTINGS
from app.core.exceptions import NotFoundError
from app.crud.availability_crud import get_user_availability
from app.models.user_setting import UserSetting
from app.schemas.availability import WeeklyAvailabilityRead
from app.schemas.user import (
    AnySettingOut,
    BooleanSettingOut,
    BooleanSettingUpdate,
    ScheduleSettingOut,
    StringSettingOut,
    StringSettingUpdate,
    UserSettingsOut,
)


def create_setting_out(
    id: int | None,
    key: str,
    value: Any,
    label: str | None,
    description: str,
    option_type: str | None,
    type_value: str,
) -> StringSettingOut | BooleanSettingOut | ScheduleSettingOut:
    """Factory to create the appropriate setting schema based on type."""
    if type_value == "boolean":
        return BooleanSettingOut(
            id=id,
            key=key,
            value=value,
            label=label,
            description=description,
            option_type=option_type,
        )
    elif type_value == "schedule":
        return ScheduleSettingOut(
            id=id,
            key=key,
            value=value,
            label=label,
            description=description,
            option_type=option_type,
        )
    else:
        return StringSettingOut(
            id=id,
            key=key,
            value=value,
            label=label,
            description=description,
            option_type=option_type,
        )


def get_user_settings(user_id: int, session: Session) -> UserSettingsOut:
    settings = session.exec(
        select(UserSetting).where(UserSetting.user_id == user_id)
    ).all()
    user_settings: list[AnySettingOut] = []
    for setting in settings:
        metadata = METADATA_SETTINGS.get(setting.key)

        if not metadata:
            raise NotFoundError(f"No metadata found for setting key: {setting.key}")

        assert setting.id is not None
        type_value = metadata.get("type", "string")
        description_value = metadata.get("description", "")
        option_type_value = metadata.get("option_type", None)

        user_settings.append(
            create_setting_out(
                id=setting.id,
                key=setting.key,
                value=setting.value,
                label=setting.label,
                description=description_value,
                option_type=option_type_value,
                type_value=type_value,
            )
        )

    user_settings.append(get_availability_setting(user_id, session))
    return UserSettingsOut(settings=user_settings)


def get_availability_setting(user_id: int, session: Session) -> AnySettingOut:
    availability = get_user_availability(user_id, session)
    av_schema = WeeklyAvailabilityRead.model_validate(availability)
    metadata = METADATA_SETTINGS.get("availability")
    if not metadata:
        raise NotFoundError("No metadata found for setting key: availability")

    type_value = metadata.get("type", "string")
    description_value = metadata.get("description", "")
    option_type_value = metadata.get("option_type", None)

    return create_setting_out(
        id=None,
        key="availability",
        value=av_schema.windows,
        label="Availability",
        description=description_value,
        option_type=option_type_value,
        type_value=type_value,
    )


def get_user_timezone(user_id: int, session: Session) -> str:
    setting = session.exec(
        select(UserSetting)
        .where(UserSetting.key == "timezone")
        .where(UserSetting.user_id == user_id)
    ).first()
    return setting.value if setting else "UTC"


def update_user_settings(
    user_id: int,
    settings: list[StringSettingUpdate | BooleanSettingUpdate],
    session: Session,
) -> None:
    for setting in settings:
        update_user_setting(user_id, setting, session)


def update_user_setting(
    user_id: int, setting: StringSettingUpdate | BooleanSettingUpdate, session: Session
) -> AnySettingOut:
    statement = (
        select(UserSetting)
        .where(UserSetting.key == setting.key)
        .where(UserSetting.user_id == user_id)
    )
    setting_model = session.exec(statement).first()
    if setting_model is None:
        raise NotFoundError(f"Setting with key {setting.key} not found")
    setting_model.value = setting.value
    setting_model.label = setting.label
    session.add(setting_model)
    session.flush()
    session.refresh(setting_model)
    assert setting_model.id is not None

    metadata = METADATA_SETTINGS.get(setting.key)
    if not metadata:
        raise NotFoundError(f"No metadata found for setting key: {setting.key}")

    type_value = metadata.get("type", "string")
    description_value = metadata.get("description", "")
    option_type_value = metadata.get("option_type", None)

    return create_setting_out(
        id=setting_model.id,
        key=setting_model.key,
        value=setting_model.value,
        label=setting_model.label,
        type_value=type_value,
        description=description_value,
        option_type=option_type_value,
    )
