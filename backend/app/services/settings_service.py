"""Service layer for settings operations, handling schema conversion and metadata."""

from typing import Any

from sqlmodel import Session

from app.core.default_settings import METADATA_SETTINGS, SettingMetadata
from app.core.exceptions import NotFoundError
from app.crud import availability_crud, setting_crud
from app.models.user_setting import UserSetting
from app.schemas.availability import WeeklyAvailabilityRead, WeeklyAvailabilityUpdate
from app.schemas.user import (
    AnySettingOut,
    BooleanSettingOut,
    BooleanSettingUpdate,
    ScheduleSettingOut,
    StringSettingOut,
    StringSettingUpdate,
    UserSettingsOut,
)


def get_setting_metadata(key: str) -> SettingMetadata:
    """Get metadata for a setting key, raising NotFoundError if not found."""
    metadata = METADATA_SETTINGS.get(key)
    if not metadata:
        raise NotFoundError(f"No metadata found for setting key: {key}")
    return metadata


def model_to_setting_out(setting: UserSetting) -> AnySettingOut:
    """Convert a UserSetting model to the appropriate setting output schema."""
    metadata = get_setting_metadata(setting.key)
    type_value = metadata.get("type", "string")
    description_value = metadata.get("description", "")
    option_type_value = metadata.get("option_type", None)

    return _create_setting_out(
        id=setting.id,
        key=setting.key,
        value=setting.value,
        label=setting.label,
        description=description_value,
        option_type=option_type_value,
        type_value=type_value,
    )


def availability_to_setting_out(
    availability: WeeklyAvailabilityRead, label: str = "Availability"
) -> ScheduleSettingOut:
    """Convert availability to a schedule setting output schema."""
    metadata = get_setting_metadata("availability")
    type_value = metadata.get("type", "schedule")
    description_value = metadata.get("description", "")
    option_type_value = metadata.get("option_type", None)

    result = _create_setting_out(
        id=None,
        key="availability",
        value=availability.windows,
        label=label,
        description=description_value,
        option_type=option_type_value,
        type_value=type_value,
    )
    # Type narrowing: we know it's ScheduleSettingOut because type_value is "schedule"
    assert isinstance(result, ScheduleSettingOut)
    return result


def get_all_user_settings(user_id: int, session: Session) -> UserSettingsOut:
    """Get all user settings including availability, converted to output schemas."""
    # Get regular settings from database
    settings = setting_crud.get_user_settings(user_id, session)
    user_settings: list[AnySettingOut] = [
        model_to_setting_out(setting) for setting in settings
    ]

    # Add availability setting
    availability = availability_crud.get_user_availability(user_id, session)
    av_schema = WeeklyAvailabilityRead.model_validate(availability)
    user_settings.append(availability_to_setting_out(av_schema))

    return UserSettingsOut(settings=user_settings)


def update_setting(
    user_id: int,
    setting: StringSettingUpdate | BooleanSettingUpdate,
    session: Session,
) -> AnySettingOut:
    """Update a setting and return the updated setting as output schema."""
    updated_model = setting_crud.update_user_setting(user_id, setting, session)
    return model_to_setting_out(updated_model)


def update_availability_setting(
    user_id: int,
    availability_update: WeeklyAvailabilityUpdate,
    session: Session,
) -> ScheduleSettingOut:
    """Update availability setting and return as schedule setting output schema."""
    updated_model = availability_crud.update_user_availability(
        user_id, availability_update, session
    )
    av_schema = WeeklyAvailabilityRead.model_validate(updated_model)
    return availability_to_setting_out(av_schema)


def get_setting_options(key: str) -> list[dict[str, str]] | None:
    """Get options for a setting key. Returns None if no options available."""
    from app.services.option_factory_service import OPTION_FACTORIES

    metadata = get_setting_metadata(key)

    # Handle static options
    if "options" in metadata and metadata.get("option_type") == "static":
        options = metadata.get("options")
        if isinstance(options, list):
            return options
        return None

    # Handle dynamic options
    if metadata.get("option_type") == "dynamic":
        factory_function = metadata.get("options")
        if isinstance(factory_function, str):
            factory_func = OPTION_FACTORIES.get(factory_function)
            if factory_func:
                return factory_func()

    return None


def _create_setting_out(
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
