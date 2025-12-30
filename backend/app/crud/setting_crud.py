from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models.user_setting import UserSetting
from app.schemas.user import BooleanSettingUpdate, StringSettingUpdate


def get_user_settings(user_id: int, session: Session) -> list[UserSetting]:
    """Get all user settings from the database."""
    return list(
        session.exec(select(UserSetting).where(UserSetting.user_id == user_id)).all()
    )


def get_user_setting(user_id: int, key: str, session: Session) -> UserSetting | None:
    """Get a specific user setting by key."""
    return session.exec(
        select(UserSetting)
        .where(UserSetting.key == key)
        .where(UserSetting.user_id == user_id)
    ).first()


def get_user_timezone(user_id: int, session: Session) -> str:
    """Get user timezone setting, defaulting to UTC if not found."""
    setting = get_user_setting(user_id, "timezone", session)
    return setting.value if setting else "UTC"


def update_user_setting(
    user_id: int,
    setting: StringSettingUpdate | BooleanSettingUpdate,
    session: Session,
) -> UserSetting:
    """Update a user setting in the database. Returns the updated model."""
    setting_model = get_user_setting(user_id, setting.key, session)
    if setting_model is None:
        raise NotFoundError(f"Setting with key {setting.key} not found")

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
