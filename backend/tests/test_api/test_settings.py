import datetime as dt

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.default_settings import DEFAULT_USER_SETTINGS, METADATA_SETTINGS
from app.models.user_setting import UserSetting


class TestGetSettings:
    """Tests for GET /settings/ endpoint."""

    def test_get_settings_default_setting(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test getting settings when user has one setting."""
        response = client.get("/settings/")

        assert response.status_code == 200
        data = response.json()
        assert "settings" in data
        assert len(data["settings"]) == len(METADATA_SETTINGS.keys())
        for setting in data["settings"]:
            assert setting["key"] in METADATA_SETTINGS.keys()
            if setting["key"] == "availability":
                assert setting["type"] == "schedule"
                for day in setting["value"].values():
                    assert len(day) == 1
                    assert day[0]["start"] == dt.time(7, 0).isoformat()
                    assert day[0]["end"] == dt.time(17, 0).isoformat()
                continue

            assert setting["value"] == DEFAULT_USER_SETTINGS[setting["key"]]["value"]
            assert setting["label"] == DEFAULT_USER_SETTINGS[setting["key"]]["label"]

    def test_get_settings_with_null_label(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test getting settings when label is null."""
        response = client.get("/settings/")

        assert response.status_code == 200
        data = response.json()
        for setting in data["settings"]:
            if setting["key"] == "split_tasks":
                assert setting["label"] is None


class TestUpdateSettings:
    """Tests for PATCH /settings/ endpoint."""

    def test_update_setting_success(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test successfully updating an existing setting."""

        update_data = {"key": "timezone", "value": "America/New_York", "label": "NYC"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "timezone"
        assert data["value"] == "America/New_York"
        assert data["label"] == "NYC"

    def test_update_setting_invalid_key(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with an invalid key returns validation error."""
        update_data = {"key": "invalid_key", "value": "some_value", "label": "Label"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 422
        # Should have validation error about invalid key

    def test_update_setting_missing_key(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with missing key field returns validation error."""
        update_data = {"value": "UTC", "label": "UTC"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 422

    def test_update_setting_missing_value(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with missing value field returns validation error."""
        update_data = {"key": "timezone", "label": "UTC"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 422

    def test_update_setting_empty_value(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating a setting with an empty value."""
        setting = UserSetting(
            user_id=mock_user_id, key="timezone", value="UTC", label="UTC"
        )
        session.add(setting)
        session.commit()

        update_data = {"key": "timezone", "value": "", "label": ""}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 200
        assert response.json()["value"] == ""
        assert response.json()["label"] == ""

    def test_update_setting_multiple_times(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating the same setting multiple times."""

        # First update
        update1 = {"key": "timezone", "value": "America/New_York", "label": "NYC"}
        response1 = client.patch("/settings/", json=update1)
        assert response1.status_code == 200
        assert response1.json()["value"] == "America/New_York"
        assert response1.json()["label"] == "NYC"

        # Second update
        update2 = {"key": "timezone", "value": "Europe/London", "label": "London"}
        response2 = client.patch("/settings/", json=update2)
        assert response2.status_code == 200
        assert response2.json()["value"] == "Europe/London"
        assert response2.json()["label"] == "London"

    def test_update_setting_different_keys(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating different setting keys."""
        # Update timezone
        update1 = {"key": "timezone", "value": "America/New_York", "label": "NYC"}
        response1 = client.patch("/settings/", json=update1)
        assert response1.status_code == 200
        assert response1.json()["key"] == "timezone"
        assert response1.json()["value"] == "America/New_York"
        assert response1.json()["label"] == "NYC"

        # Update language
        update2 = {"key": "language", "value": "fr", "label": "French"}
        response2 = client.patch("/settings/", json=update2)
        assert response2.status_code == 200
        assert response2.json()["key"] == "language"
        assert response2.json()["value"] == "fr"
        assert response2.json()["label"] == "French"

        # Verify both are updated
        get_response = client.get("/settings/")
        assert get_response.status_code == 200
        settings_data = get_response.json()["settings"]
        values = {s["key"]: s["value"] for s in settings_data}
        labels = {s["key"]: s["label"] for s in settings_data}
        assert values["timezone"] == "America/New_York"
        assert values["language"] == "fr"
        assert labels["timezone"] == "NYC"
        assert labels["language"] == "French"

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
        update_data = {"key": "timezone", "value": 123, "label": "Test"}
        response = client.patch("/settings/", json=update_data)

        # Pydantic should coerce it to string or return 422
        # Let's see what happens - it might work if Pydantic coerces
        assert response.status_code in [200, 422]

    def test_update_setting_wrong_type_key(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test updating with wrong type for key field."""
        update_data = {"key": 123, "value": "UTC", "label": "UTC"}
        response = client.patch("/settings/", json=update_data)

        # Should return 422 for invalid key type
        assert response.status_code == 422

    def test_update_setting_with_null_label(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating a setting with null label."""
        setting = UserSetting(
            user_id=mock_user_id, key="timezone", value="UTC", label="UTC"
        )
        session.add(setting)
        session.commit()

        update_data = {"key": "timezone", "value": "America/New_York", "label": None}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 200
        assert response.json()["value"] == "America/New_York"
        assert response.json()["label"] is None

    def test_update_setting_without_label(
        self, client: TestClient, session: Session, mock_user_id: int
    ) -> None:
        """Test updating a setting without providing label (should be optional)."""
        setting = UserSetting(
            user_id=mock_user_id, key="timezone", value="UTC", label="UTC"
        )
        session.add(setting)
        session.commit()

        # Don't include label in update - it's optional
        update_data = {"key": "timezone", "value": "America/New_York"}
        response = client.patch("/settings/", json=update_data)

        assert response.status_code == 200
        assert response.json()["value"] == "America/New_York"
        # Label should be None since we didn't provide it
        assert response.json()["label"] is None


class TestGetOptions:
    """Tests for GET /settings/options/{key} endpoint."""

    def test_get_timezone_options_success(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test getting options for a valid key."""
        import pytz

        response = client.get("/settings/options/timezone")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for option in data:
            assert option["value"] in pytz.common_timezones
            assert option["label"] == option["value"].replace("/", " ")

    def test_get_language_options_success(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test getting options for a valid key."""
        from app.core.default_settings import METADATA_SETTINGS

        language_options = METADATA_SETTINGS["language"]["options"]
        assert language_options is not None
        assert isinstance(language_options, list)
        assert len(language_options) > 0
        response = client.get("/settings/options/language")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for option in data:
            assert option["value"] in [o["value"] for o in language_options]
            assert option["label"] in [o["label"] for o in language_options]

    def test_get_options_invalid_key(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test getting options for an invalid key."""
        response = client.get("/settings/options/invalid_key")
        assert response.status_code == 404

    def test_get_options_with_no_options(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test getting options for a setting with no options."""
        response = client.get("/settings/options/allow_task_splitting")
        assert response.status_code == 200
        assert response.json() is None
