from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user_setting import UserSetting


class TestGetSettings:
    """Tests for GET /settings/ endpoint."""

    def test_get_settings_empty(self, client: TestClient, mock_user_id: int) -> None:
        """Test getting settings when user has no settings."""
        response = client.get("/settings/")

        assert response.status_code == 200
        data = response.json()
        assert "settings" in data
        assert data["settings"] == []

    def test_get_settings_single_setting(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test getting settings when user has one setting."""
        setting = UserSetting(user_id=mock_user_id, key="timezone", value="UTC")
        session.add(setting)
        session.commit()

        response = client.get("/settings/")

        assert response.status_code == 200
        data = response.json()
        assert "settings" in data
        assert len(data["settings"]) == 1
        assert data["settings"][0]["key"] == "timezone"
        assert data["settings"][0]["value"] == "UTC"
        assert data["settings"][0]["id"] is not None

    def test_get_settings_multiple_settings(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test getting settings when user has multiple settings."""
        settings = [
            UserSetting(user_id=mock_user_id, key="timezone", value="UTC"),
            UserSetting(user_id=mock_user_id, key="language", value="en"),
        ]
        for setting in settings:
            session.add(setting)
        session.commit()

        response = client.get("/settings/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["settings"]) == 2
        keys = {s["key"] for s in data["settings"]}
        assert keys == {"timezone", "language"}

    def test_get_settings_only_returns_current_user_settings(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test that settings endpoint only returns settings for authenticated user."""
        from app.models.user import User

        # First create the authenticated user (will get ID 1, matching mock_user_id)
        authenticated_user = User(
            email="authenticated@example.com", password="password"
        )
        session.add(authenticated_user)
        session.commit()
        session.refresh(authenticated_user)
        # Verify it got the expected ID
        assert authenticated_user.id == mock_user_id  # type: ignore[attr-defined]

        # Create another user (will get ID 2, a different ID)
        other_user = User(email="other@example.com", password="password")
        session.add(other_user)
        session.commit()
        session.refresh(other_user)
        # Verify it got a different ID
        assert other_user.id != mock_user_id  # type: ignore[attr-defined]

        # Create settings for both users
        user_setting = UserSetting(user_id=mock_user_id, key="timezone", value="UTC")
        other_setting = UserSetting(
            user_id=other_user.id,  # type: ignore[attr-defined]
            key="timezone",
            value="America/Los_Angeles",
        )
        session.add(user_setting)
        session.add(other_setting)
        session.commit()

        response = client.get("/settings/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["settings"]) == 1
        assert data["settings"][0]["value"] == "UTC"


class TestUpdateSettings:
    """Tests for PATCH /settings/ endpoint."""

    def test_update_setting_success(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test successfully updating an existing setting."""
        setting = UserSetting(user_id=mock_user_id, key="timezone", value="UTC")
        session.add(setting)
        session.commit()
        session.refresh(setting)

        update_data = {"key": "timezone", "value": "America/New_York"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "timezone"
        assert data["value"] == "America/New_York"
        assert data["id"] == setting.id

        # Verify database was updated
        session.refresh(setting)
        assert setting.value == "America/New_York"

    def test_update_setting_not_found(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating a setting that doesn't exist returns error.

        Note: This shouldn't occur in normal operation since default settings
        are created on user registration. This test ensures defensive error handling.
        """
        update_data = {"key": "timezone", "value": "UTC"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_setting_invalid_key(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with an invalid key returns validation error."""
        update_data = {"key": "invalid_key", "value": "some_value"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 422
        # Should have validation error about invalid key

    def test_update_setting_missing_key(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with missing key field returns validation error."""
        update_data = {"value": "UTC"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 422

    def test_update_setting_missing_value(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with missing value field returns validation error."""
        update_data = {"key": "timezone"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 422

    def test_update_setting_empty_value(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating a setting with an empty value."""
        setting = UserSetting(user_id=mock_user_id, key="timezone", value="UTC")
        session.add(setting)
        session.commit()

        update_data = {"key": "timezone", "value": ""}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 200
        assert response.json()["value"] == ""

    def test_update_setting_multiple_times(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating the same setting multiple times."""
        setting = UserSetting(user_id=mock_user_id, key="timezone", value="UTC")
        session.add(setting)
        session.commit()
        session.refresh(setting)
        setting_id = setting.id

        # First update
        update1 = {"key": "timezone", "value": "America/New_York"}
        response1 = client.patch("/settings/", json=update1)
        assert response1.status_code == 200
        assert response1.json()["value"] == "America/New_York"
        assert response1.json()["id"] == setting_id

        # Second update
        update2 = {"key": "timezone", "value": "Europe/London"}
        response2 = client.patch("/settings/", json=update2)
        assert response2.status_code == 200
        assert response2.json()["value"] == "Europe/London"
        assert response2.json()["id"] == setting_id

    def test_update_setting_different_keys(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating different setting keys."""
        settings = [
            UserSetting(user_id=mock_user_id, key="timezone", value="UTC"),
            UserSetting(user_id=mock_user_id, key="language", value="en"),
        ]
        for setting in settings:
            session.add(setting)
        session.commit()

        # Update timezone
        update1 = {"key": "timezone", "value": "America/New_York"}
        response1 = client.patch("/settings/", json=update1)
        assert response1.status_code == 200
        assert response1.json()["key"] == "timezone"
        assert response1.json()["value"] == "America/New_York"

        # Update language
        update2 = {"key": "language", "value": "fr"}
        response2 = client.patch("/settings/", json=update2)
        assert response2.status_code == 200
        assert response2.json()["key"] == "language"
        assert response2.json()["value"] == "fr"

        # Verify both are updated
        get_response = client.get("/settings/")
        assert get_response.status_code == 200
        settings_data = get_response.json()["settings"]
        values = {s["key"]: s["value"] for s in settings_data}
        assert values["timezone"] == "America/New_York"
        assert values["language"] == "fr"

    def test_update_setting_wrong_user(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test that updating a setting for a different user fails."""
        from app.models.user import User

        # First create the authenticated user (will get ID 1, matching mock_user_id)
        authenticated_user = User(
            email="authenticated@example.com", password="password"
        )
        session.add(authenticated_user)
        session.commit()
        session.refresh(authenticated_user)
        # Verify it got the expected ID
        assert authenticated_user.id == mock_user_id  # type: ignore[attr-defined]

        # Create another user (will get ID 2, a different ID)
        other_user = User(email="other@example.com", password="password")
        session.add(other_user)
        session.commit()
        session.refresh(other_user)
        # Verify it got a different ID
        assert other_user.id != mock_user_id  # type: ignore[attr-defined]

        # Create setting for other user
        other_setting = UserSetting(
            user_id=other_user.id,  # type: ignore[attr-defined]
            key="timezone",
            value="UTC",
        )
        session.add(other_setting)
        session.commit()

        # Try to update it as the authenticated user
        update_data = {"key": "timezone", "value": "America/New_York"}
        response = client.patch("/settings/", json=update_data)

        # Should fail because the setting doesn't exist for the authenticated user
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_setting_invalid_json(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with invalid JSON returns error."""
        response = client.patch("/settings/", json="not valid json")

        # FastAPI will return 422 for invalid JSON structure
        assert response.status_code == 422

    def test_update_setting_wrong_type_value(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with wrong type for value field."""
        # Value should be a string, but we'll try sending a number
        update_data = {"key": "timezone", "value": 123}
        response = client.patch("/settings/", json=update_data)

        # Pydantic should coerce it to string or return 422
        # Let's see what happens - it might work if Pydantic coerces
        assert response.status_code in [200, 422]

    def test_update_setting_wrong_type_key(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with wrong type for key field."""
        update_data = {"key": 123, "value": "UTC"}
        response = client.patch("/settings/", json=update_data)

        # Should return 422 for invalid key type
        assert response.status_code == 422
