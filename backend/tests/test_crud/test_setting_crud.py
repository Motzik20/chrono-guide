from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.crud import setting_crud
from app.models.user import User
from app.models.user_setting import UserSetting
from app.schemas.user import UserSettingOut, UserSettingsOut, UserSettingUpdate


class TestGetUserSettings:
    """Tests for get_user_settings function."""

    def test_get_user_settings_empty(self, session: Session, user: User) -> None:
        """Test getting settings for a user with no settings returns empty list."""
        assert user.id is not None
        result = setting_crud.get_user_settings(user.id, session)

        assert isinstance(result, UserSettingsOut)
        assert result.settings == []

    def test_get_user_settings_single_setting(
        self, session: Session, user: User
    ) -> None:
        """Test getting settings for a user with one setting."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="America/New_York",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        result = setting_crud.get_user_settings(user.id, session)

        assert isinstance(result, UserSettingsOut)
        assert len(result.settings) == 1
        assert result.settings[0].key == "timezone"
        assert result.settings[0].value == "America/New_York"
        assert result.settings[0].id == setting.id

    def test_get_user_settings_multiple_settings(
        self, session: Session, user: User
    ) -> None:
        """Test getting settings for a user with multiple settings."""
        assert user.id is not None
        settings = [
            UserSetting(
                user_id=user.id,
                key="timezone",
                value="America/New_York",
            ),
            UserSetting(
                user_id=user.id,
                key="language",
                value="en",
            ),
        ]
        for setting in settings:
            session.add(setting)
        session.commit()
        for setting in settings:
            session.refresh(setting)

        result = setting_crud.get_user_settings(user.id, session)

        assert isinstance(result, UserSettingsOut)
        assert len(result.settings) == 2
        keys = {s.key for s in result.settings}
        assert keys == {"timezone", "language"}

    def test_get_user_settings_only_returns_user_settings(
        self, session: Session, user: User
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
        )
        other_setting = UserSetting(
            user_id=other_user.id,
            key="timezone",
            value="America/Los_Angeles",
        )
        session.add(user_setting)
        session.add(other_setting)
        session.commit()
        session.refresh(user_setting)
        session.refresh(other_setting)

        result = setting_crud.get_user_settings(user.id, session)

        assert len(result.settings) == 1
        assert result.settings[0].value == "UTC"
        assert result.settings[0].id == user_setting.id

    def test_get_user_settings_filters_none_ids(
        self, session: Session, user: User
    ) -> None:
        """Test that settings with None IDs are filtered out."""
        # This shouldn't happen in practice, but test the edge case
        assert user.id is not None
        setting_with_none_id = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
        )
        setting_with_none_id.id = None

        # Mock the session.exec() to return a setting with None ID
        mock_result = MagicMock()
        mock_result.all.return_value = [setting_with_none_id]
        session.exec = MagicMock(return_value=mock_result)

        result = setting_crud.get_user_settings(user.id, session)

        # Should filter out None IDs
        assert len(result.settings) == 0


class TestUpdateUserSetting:
    """Tests for update_user_setting function."""

    def test_update_user_setting_success(self, session: Session, user: User) -> None:
        """Test successfully updating an existing setting."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = UserSettingUpdate(key="timezone", value="America/New_York")
        assert user.id is not None
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        assert isinstance(result, UserSettingOut)
        assert result.key == "timezone"
        assert result.value == "America/New_York"
        assert result.id == setting.id

        # Verify the database was updated
        session.refresh(setting)
        assert setting.value == "America/New_York"

    def test_update_user_setting_not_found(self, session: Session, user: User) -> None:
        """Test updating a setting that doesn't exist raises NotFoundError."""
        update = UserSettingUpdate(key="timezone", value="UTC")
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
        )
        session.add(other_setting)
        session.commit()
        session.refresh(other_setting)

        # Try to update it as the first user
        update = UserSettingUpdate(key="timezone", value="America/New_York")
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
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        # First update
        update1 = UserSettingUpdate(key="timezone", value="America/New_York")
        assert user.id is not None
        result1 = setting_crud.update_user_setting(
            user.id,
            update1,
            session,
        )
        assert result1.value == "America/New_York"

        # Second update
        update2 = UserSettingUpdate(key="timezone", value="Europe/London")
        assert user.id is not None
        result2 = setting_crud.update_user_setting(
            user.id,
            update2,
            session,
        )
        assert result2.value == "Europe/London"
        assert result2.id == result1.id  # Same setting, same ID

    def test_update_user_setting_different_keys(
        self, session: Session, user: User
    ) -> None:
        """Test updating different setting keys."""
        assert user.id is not None
        settings = [
            UserSetting(
                user_id=user.id,
                key="timezone",
                value="UTC",
            ),
            UserSetting(
                user_id=user.id,
                key="language",
                value="en",
            ),
        ]
        for setting in settings:
            session.add(setting)
        session.commit()
        for setting in settings:
            session.refresh(setting)

        # Update timezone
        update1 = UserSettingUpdate(key="timezone", value="America/New_York")
        assert user.id is not None
        result1 = setting_crud.update_user_setting(
            user.id,
            update1,
            session,
        )
        assert result1.key == "timezone"
        assert result1.value == "America/New_York"

        # Update language
        update2 = UserSettingUpdate(key="language", value="fr")
        assert user.id is not None
        result2 = setting_crud.update_user_setting(
            user.id,
            update2,
            session,
        )
        assert result2.key == "language"
        assert result2.value == "fr"

        # Verify both are updated
        all_settings = setting_crud.get_user_settings(
            user.id,
            session,
        )
        assert len(all_settings.settings) == 2
        values = {s.key: s.value for s in all_settings.settings}
        assert values["timezone"] == "America/New_York"
        assert values["language"] == "fr"

    def test_update_user_setting_empty_value(
        self, session: Session, user: User
    ) -> None:
        """Test updating a setting with an empty value."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = UserSettingUpdate(key="timezone", value="")
        assert user.id is not None
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        assert result.value == ""
        session.refresh(setting)
        assert setting.value == ""

    def test_update_user_setting_id_after_flush(
        self, session: Session, user: User
    ) -> None:
        """Test that setting has an ID after flush."""
        assert user.id is not None
        setting = UserSetting(
            user_id=user.id,
            key="timezone",
            value="UTC",
        )
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update = UserSettingUpdate(key="timezone", value="America/New_York")
        assert user.id is not None
        result = setting_crud.update_user_setting(
            user.id,
            update,
            session,
        )

        # Should have an ID (this tests the SystemError check in the function)
        assert result.id is not None
