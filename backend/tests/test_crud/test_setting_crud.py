import pytest
from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.crud import setting_crud
from app.models.user import User
from app.models.user_setting import UserSetting
from app.schemas.user import (
    StringSettingOut,
    StringSettingUpdate,
    UserSettingsOut,
)


class TestGetUserSettings:
    """Tests for get_user_settings function."""

    def test_get_user_settings_no_availability(
        self, session: Session, user: User
    ) -> None:
        """Test getting settings for a user with no settings returns empty list."""
        assert user.id is not None
        with pytest.raises(NotFoundError, match="No availability found for user"):
            setting_crud.get_user_settings(user.id, session)

    def test_get_user_settings_single_setting(
        self, session: Session, user: User, daily_windows: None
    ) -> None:
        """Test getting settings for a user with one setting."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="America/New_York",
            label="New York",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        result = setting_crud.get_user_settings(user.id, session)

        assert isinstance(result, UserSettingsOut)
        assert len(result.settings) == 2
        assert result.settings[0].key == "timezone"
        assert result.settings[0].value == "America/New_York"
        assert result.settings[0].label == "New York"
        assert result.settings[0].id == setting.id

    def test_get_user_settings_multiple_settings(
        self, session: Session, user: User, daily_windows: None
    ) -> None:
        """Test getting settings for a user with multiple settings."""
        assert user.id is not None
        settings = [
            UserSetting(
                user_id=user.id,
                key="timezone",
                value="America/New_York",
                label="New York",
            ),
            UserSetting(
                user_id=user.id,
                key="language",
                value="en",
                label="English",
            ),
        ]
        for setting in settings:
            session.add(setting)
        session.commit()
        for setting in settings:
            session.refresh(setting)

        result = setting_crud.get_user_settings(user.id, session)

        assert isinstance(result, UserSettingsOut)
        assert len(result.settings) == 3
        keys = {s.key for s in result.settings}
        assert keys == {"timezone", "language", "availability"}

    def test_get_user_settings_only_returns_user_settings(
        self, session: Session, user: User, daily_windows: None
    ) -> None:
        """Test that get_user_settings only returns settings for the specified user."""
        # Create another user
        other_user = User(email="other@example.com", password="password")
        session.add(other_user)
        session.commit()
        session.refresh(other_user)
        assert other_user.id is not None
        assert user.id is not None
        # Create settings for both users
        user_setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
            label="UTC",
        )
        other_setting = UserSetting(
            user_id=other_user.id,
            key="timezone",
            value="America/Los_Angeles",
            label="Los Angeles",
        )
        session.add(user_setting)
        session.add(other_setting)
        session.commit()
        session.refresh(user_setting)
        session.refresh(other_setting)

        result = setting_crud.get_user_settings(user.id, session)

        assert len(result.settings) == 2
        assert result.settings[0].value == "UTC"
        assert result.settings[0].label == "UTC"
        assert result.settings[0].id == user_setting.id

    def test_get_user_settings_with_null_label(
        self, session: Session, user: User, daily_windows: None
    ) -> None:
        """Test getting settings when label is null."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
            label=None,
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        result = setting_crud.get_user_settings(user.id, session)

        assert len(result.settings) == 2
        assert result.settings[0].label is None


class TestUpdateUserSetting:
    """Tests for update_user_setting function."""

    def test_update_user_setting_success(self, session: Session, user: User) -> None:
        """Test successfully updating an existing setting."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
            label="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = StringSettingUpdate(
            key="timezone", value="America/New_York", label="New York"
        )
        assert user.id is not None
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        assert isinstance(result, StringSettingOut)
        assert result.key == "timezone"
        assert result.value == "America/New_York"
        assert result.label == "New York"
        assert result.id == setting.id

        # Verify the database was updated
        session.refresh(setting)
        assert setting.value == "America/New_York"
        assert setting.label == "New York"

    def test_update_user_setting_not_found(self, session: Session, user: User) -> None:
        """Test updating a setting that doesn't exist raises NotFoundError."""
        update = StringSettingUpdate(key="timezone", value="UTC", label="UTC")
        assert user.id is not None
        with pytest.raises(NotFoundError, match="Setting with key timezone not found"):
            setting_crud.update_user_setting(
                user.id,
                update,
                session,
            )

    def test_update_user_setting_wrong_user(self, session: Session, user: User) -> None:
        """Test that updating a setting for a different user raises NotFoundError."""
        from app.models.user import User

        other_user = User(email="other@example.com", password="password")
        session.add(other_user)
        session.commit()
        session.refresh(other_user)
        assert other_user.id is not None
        # Create setting for other user
        other_setting = UserSetting(
            user_id=other_user.id,
            key="timezone",
            value="UTC",
            label="UTC",
        )
        session.add(other_setting)
        session.commit()
        session.refresh(other_setting)

        # Try to update it as the first user
        update = StringSettingUpdate(
            key="timezone", value="America/New_York", label="New York"
        )
        assert user.id is not None
        with pytest.raises(NotFoundError, match="Setting with key timezone not found"):
            setting_crud.update_user_setting(
                user.id,
                update,
                session,
            )

    def test_update_user_setting_multiple_updates(
        self, session: Session, user: User
    ) -> None:
        """Test updating the same setting multiple times."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
            label="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        # First update
        update1 = StringSettingUpdate(
            key="timezone", value="America/New_York", label="New York"
        )
        assert user.id is not None
        result1 = setting_crud.update_user_setting(
            user.id,
            update1,
            session,
        )
        assert result1.value == "America/New_York"
        assert result1.label == "New York"

        # Second update
        update2 = StringSettingUpdate(
            key="timezone", value="Europe/London", label="London"
        )
        assert user.id is not None
        result2 = setting_crud.update_user_setting(
            user.id,
            update2,
            session,
        )
        assert result2.value == "Europe/London"
        assert result2.label == "London"
        assert result2.id == result1.id  # Same setting, same ID

    def test_update_user_setting_different_keys(
        self, session: Session, user: User, daily_windows: None
    ) -> None:
        """Test updating different setting keys."""
        assert user.id is not None
        settings = [
            UserSetting(
                user_id=user.id,
                key="timezone",
                value="UTC",
                label="UTC",
            ),
            UserSetting(
                user_id=user.id,
                key="language",
                value="en",
                label="English",
            ),
        ]
        for setting in settings:
            session.add(setting)
        session.commit()
        for setting in settings:
            session.refresh(setting)

        # Update timezone
        update1 = StringSettingUpdate(
            key="timezone", value="America/New_York", label="New York"
        )
        assert user.id is not None
        result1 = setting_crud.update_user_setting(
            user.id,
            update1,
            session,
        )
        assert result1.key == "timezone"
        assert result1.value == "America/New_York"
        assert result1.label == "New York"

        # Update language
        update2 = StringSettingUpdate(key="language", value="fr", label="French")
        assert user.id is not None
        result2 = setting_crud.update_user_setting(
            user.id,
            update2,
            session,
        )
        assert result2.key == "language"
        assert result2.value == "fr"
        assert result2.label == "French"

        # Verify both are updated
        all_settings = setting_crud.get_user_settings(
            user.id,
            session,
        )
        assert len(all_settings.settings) == 3
        values = {s.key: s.value for s in all_settings.settings}
        labels = {s.key: s.label for s in all_settings.settings}
        assert values["timezone"] == "America/New_York"
        assert values["language"] == "fr"
        assert labels["timezone"] == "New York"
        assert labels["language"] == "French"

    def test_update_user_setting_empty_value(
        self, session: Session, user: User
    ) -> None:
        """Test updating a setting with an empty value."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
            label="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = StringSettingUpdate(key="timezone", value="", label="")
        assert user.id is not None
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        assert result.value == ""
        assert result.label == ""
        session.refresh(setting)
        assert setting.value == ""
        assert setting.label == ""

    def test_update_user_setting_id_after_flush(
        self, session: Session, user: User
    ) -> None:
        """Test that setting has an ID after flush."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
            label="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = StringSettingUpdate(
            key="timezone", value="America/New_York", label="New York"
        )
        assert user.id is not None
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        # Should have an ID (this tests the SystemError check in the function)
        assert result.id is not None

    def test_update_user_setting_with_null_label(
        self, session: Session, user: User
    ) -> None:
        """Test updating a setting with null label."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
            label="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = StringSettingUpdate(
            key="timezone", value="America/New_York", label=None
        )
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        assert result.value == "America/New_York"
        assert result.label is None
        session.refresh(setting)
        assert setting.label is None

    def test_update_user_setting_only_label(self, session: Session, user: User) -> None:
        """Test updating only the label while keeping the same value."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="America/New_York",
            label="New York",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = StringSettingUpdate(
            key="timezone", value="America/New_York", label="NYC", type="string"
        )
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        assert result.value == "America/New_York"
        assert result.label == "NYC"
        session.refresh(setting)
        assert setting.label == "NYC"
