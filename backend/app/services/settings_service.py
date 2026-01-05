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
    ScheduleSettingUpdate,
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
    setting: StringSettingUpdate | BooleanSettingUpdate | ScheduleSettingUpdate,
    session: Session,
) -> AnySettingOut:
    """Update a setting and return the updated setting as output schema."""
    if setting.type == "schedule":
        availability_update = WeeklyAvailabilityUpdate.model_validate(
            {"windows": setting.value}
        )
        return update_availability_setting(user_id, availability_update, session)
    elif setting.key == "timezone":
        old_timezone = setting_crud.get_user_setting(user_id, "timezone", session).value
        new_timezone = setting.value
        if old_timezone != new_timezone:
            _reschedule(user_id, new_timezone, session)
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


def _reschedule(user_id: int, new_timezone: str, session: Session):
    from sqlmodel import select

    from app.core.timezone import now_utc
    from app.crud import availability_crud, schedule_item_crud, setting_crud, task_crud
    from app.models.schedule_item import ScheduleItem
    from app.services.greedy_scheduler import GreedyScheduler
    from app.services.protocols import ChronoScheduler
    from app.services.scheduling_utils import schedule_blocks_to_schedule_items

    # Get all scheduled tasks
    scheduled_tasks = task_crud.get_scheduled_tasks(user_id, session)

    if not scheduled_tasks:
        return  # No tasks to reschedule

    task_ids = [task.id for task in scheduled_tasks if task.id is not None]

    existing_schedule_items = session.exec(
        select(ScheduleItem)
        .where(ScheduleItem.user_id == user_id)
        .where(ScheduleItem.task_id.in_(task_ids))  # type: ignore[attr-defined]
        .where(ScheduleItem.source == "task")
    ).all()

    for item in existing_schedule_items:
        session.delete(item)

    session.flush()

    availability = availability_crud.get_user_availability(user_id, session)
    schedule_config = setting_crud.get_schedule_config(user_id, session)
    schedule_config.timezone = new_timezone

    all_schedule_items = schedule_item_crud.get_user_schedule_items(user_id, session)

    scheduler: ChronoScheduler = GreedyScheduler()
    response = scheduler.schedule_tasks(
        scheduled_tasks,
        all_schedule_items,
        availability,
        schedule_config,
    )

    if response.schedule_blocks:
        schedule_items_to_create = schedule_blocks_to_schedule_items(
            response.schedule_blocks, user_id
        )
        schedule_item_crud.create_schedule_items(schedule_items_to_create, session)

        task_crud.update_tasks_scheduled_at(
            task_ids,
            now_utc(),
            user_id,
            session,
        )

    session.commit()


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
