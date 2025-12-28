from sqlmodel import Session, select

from app.core.default_settings import METADATA_SETTINGS
from app.core.exceptions import NotFoundError
from app.models.user_setting import UserSetting
from app.schemas.user import UserSettingOut, UserSettingsOut, UserSettingUpdate


def get_user_settings(user_id: int, session: Session) -> UserSettingsOut:
    settings = session.exec(
        select(UserSetting).where(UserSetting.user_id == user_id)
    ).all()
    user_settings: list[UserSettingOut] = []
    for setting in settings:
        metadata = METADATA_SETTINGS.get(setting.key)

        if not metadata:
            raise NotFoundError(f"No metadata found for setting key: {setting.key}")

        assert setting.id is not None
        type_value = metadata.get("type", "string")
        description_value = metadata.get("description", "")
        option_type_value = metadata.get("option_type", None)

        user_settings.append(
            UserSettingOut(
                id=setting.id,
                key=setting.key,
                value=setting.value,
                label=setting.label,
                type=type_value,
                description=description_value,
                option_type=option_type_value,
            )
        )
    return UserSettingsOut(settings=user_settings)


def update_user_settings(
    user_id: int, settings: list[UserSettingUpdate], session: Session
) -> None:
    for setting in settings:
        update_user_setting(user_id, setting, session)


def update_user_setting(
    user_id: int, setting: UserSettingUpdate, session: Session
) -> UserSettingOut:
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

    return UserSettingOut(
        id=setting_model.id,
        key=setting_model.key,
        value=setting_model.value,
        label=setting_model.label,
        type=type_value,
        description=description_value,
        option_type=option_type_value,
    )
