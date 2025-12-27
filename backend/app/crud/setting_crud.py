from sqlmodel import Session, select

from app.models.user_setting import UserSetting
from app.schemas.user import UserSettingOut, UserSettingsOut, UserSettingUpdate


def get_user_settings(user_id: int, session: Session) -> UserSettingsOut:
    settings = session.exec(
        select(UserSetting).where(UserSetting.user_id == user_id)
    ).all()
    return UserSettingsOut(
        settings=[
            UserSettingOut(id=setting.id, key=setting.key, value=setting.value)
            for setting in settings
            if setting.id is not None
        ]
    )


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
        raise ValueError(f"Setting with key {setting.key} not found")
    setting_model.value = setting.value
    session.add(setting_model)
    session.flush()
    session.refresh(setting_model)
    if setting_model.id is None:
        raise ValueError(f"Setting with key {setting.key} has no ID after flush")
    return UserSettingOut(
        id=setting_model.id, key=setting_model.key, value=setting_model.value
    )
