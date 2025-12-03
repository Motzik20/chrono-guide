import pytest
from sqlmodel import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut, UserUpdate


class TestUser:
    def test_db_model(self, session: Session) -> None:
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

    def test_create(self) -> None:
        user_create = UserCreate(email="newuser@example.com", password="newpassword123")

        assert user_create.email == "newuser@example.com"
        assert user_create.password == "newpassword123"

    def test_update(self, session: Session, user: User) -> None:
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

    def test_read(self, user: User) -> None:
        user_read = UserOut.model_validate(user)

        assert user_read.id == user.id  # type: ignore[attr-defined]
        assert user_read.email == user.email
        assert user_read.created_at == user.created_at  # type: ignore[attr-defined]
        assert user_read.updated_at == user.updated_at  # type: ignore[attr-defined]

        # Test that the Read DTO can be serialized to JSON
        json_data = user_read.model_dump()
        assert "id" in json_data
        assert "email" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

        read_from_dict = UserOut.model_validate(json_data)
        assert read_from_dict.id == user.id  # type: ignore[attr-defined]
        assert read_from_dict.email == user.email

    def test_login(self) -> None:
        user_login = UserLogin(email="login@example.com", password="loginpassword123")

        assert user_login.email == "login@example.com"
        assert user_login.password == "loginpassword123"

    def test_create_invalid_email(self) -> None:
        with pytest.raises(ValueError, match="Email must contain @"):
            UserCreate(email="invalid-email", password="password123")

    def test_create_empty_email(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(email="", password="password123")

    def test_create_empty_password(self) -> None:
        with pytest.raises(ValueError):
            UserCreate(email="test@example.com", password="")

    def test_email_normalization(self) -> None:
        user_create = UserCreate(email="TEST@EXAMPLE.COM", password="password123")

        assert user_create.email == "test@example.com"

    def test_model_validator_non_dict_data(self) -> None:
        result = User.convert_datetimes_to_utc(  # type: ignore[attr-defined]
            {"email": "test@mail.com", "password": "test"}
        )
        assert isinstance(result, dict)
        assert result["password"] == "test"
