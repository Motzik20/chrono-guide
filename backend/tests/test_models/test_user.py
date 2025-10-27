import pytest

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut, UserUpdate


class TestUser:
    def test_db_model(self, session):
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
        }

        user = User.model_validate(user_data)
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password == "testpassword123"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_create(self):
        user_create = UserCreate(email="newuser@example.com", password="newpassword123")

        assert user_create.email == "newuser@example.com"
        assert user_create.password == "newpassword123"

    def test_update(self, session, user):
        original_email = user.email

        user_update = UserUpdate(email="updated@example.com")

        update_data = user_update.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.email == "updated@example.com"
        assert user.email != original_email

    def test_read(self, user):
        # Test converting SQLModel to Pydantic Read DTO
        user_read = UserOut.model_validate(user)

        # Verify all fields are properly mapped
        assert user_read.id == user.id
        assert user_read.email == user.email
        assert user_read.created_at == user.created_at
        assert user_read.updated_at == user.updated_at

        # Test that the Read DTO can be serialized to JSON
        json_data = user_read.model_dump()
        assert "id" in json_data
        assert "email" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

        # Test creating Read DTO from dict (simulating API response)
        read_from_dict = UserOut.model_validate(json_data)
        assert read_from_dict.id == user.id
        assert read_from_dict.email == user.email

    def test_login(self):
        user_login = UserLogin(email="login@example.com", password="loginpassword123")

        assert user_login.email == "login@example.com"
        assert user_login.password == "loginpassword123"

    def test_create_invalid_email(self):
        with pytest.raises(ValueError, match="Email must contain @"):
            UserCreate(email="invalid-email", password="password123")

    def test_create_empty_email(self):
        with pytest.raises(ValueError):
            UserCreate(email="", password="password123")

    def test_create_empty_password(self):
        with pytest.raises(ValueError):
            UserCreate(email="test@example.com", password="")

    def test_email_normalization(self):
        user_create = UserCreate(email="TEST@EXAMPLE.COM", password="password123")

        assert user_create.email == "test@example.com"

    def test_model_validator_non_dict_data(self):
        """Test that the model validator handles non-dict data correctly."""
        result = User.convert_datetimes_to_utc(None)
        assert result is None

        result = User.convert_datetimes_to_utc("not a dict")
        assert result == "not a dict"

        result = User.convert_datetimes_to_utc(
            {"email": "test@mail.com", "password": "test"}
        )
        assert isinstance(result, dict)
        assert result["password"] == "test"
