from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models.user_setting import UserSetting
from app.schemas.user import BooleanSettingUpdate, StringSettingUpdate
from app.services.scheduling_types import SchedulingConfig


def get_user_settings(user_id: int, session: Session) -> list[UserSetting]:
    """Get all user settings from the database."""
    return list(
        session.exec(select(UserSetting).where(UserSetting.user_id == user_id)).all()
    )


def get_user_setting(user_id: int, key: str, session: Session) -> UserSetting:
    """Get a specific user setting by key."""
    setting = session.exec(
        select(UserSetting)
        .where(UserSetting.key == key)
        .where(UserSetting.user_id == user_id)
    ).first()
    if not setting:
        raise NotFoundError(f"Setting with key {key} not found")
    return setting


def get_user_timezone(user_id: int, session: Session) -> str:
    """Get user timezone setting, defaulting to UTC if not found."""
    setting = get_user_setting(user_id, "timezone", session)
    return setting.value if setting else "UTC"


def get_bool_setting(user_id: int, key: str, session: Session) -> bool:
    setting = get_user_setting(user_id, key, session)
    return False if setting.value == "false" else True


def update_user_setting(
    user_id: int,
    setting: StringSettingUpdate | BooleanSettingUpdate,
    session: Session,
) -> UserSetting:
    """Update a user setting in the database. Returns the updated model."""
    setting_model = get_user_setting(user_id, setting.key, session)
    setting_model.value = setting.value
    setting_model.label = setting.label
    session.add(setting_model)
    session.flush()
    session.refresh(setting_model)
    return setting_model


def update_user_settings(
    user_id: int,
    settings: list[StringSettingUpdate | BooleanSettingUpdate],
    session: Session,
) -> list[UserSetting]:
    """Update multiple user settings. Returns the updated models."""
    return [update_user_setting(user_id, setting, session) for setting in settings]


def get_schedule_config(user_id: int, session: Session) -> SchedulingConfig:
    """Get the schedule configuration for a user."""
    allow_splitting = get_bool_setting(user_id, "allow_task_splitting", session)
    return SchedulingConfig(
        max_scheduling_weeks=12,  # TODO: Make this configurable
        allow_splitting=allow_splitting,
        timezone=get_user_timezone(user_id, session),
    )
