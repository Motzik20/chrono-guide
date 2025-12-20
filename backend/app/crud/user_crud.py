from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin


def create_user(user: UserCreate, session: Session) -> User:
    user_model: User = User.model_validate(user)
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    session.add(user_model)
    session.flush()
    session.refresh(user_model)
    return user_model

def login(user: UserLogin, session: Session) -> dict[str, str]:
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if not existing_user:
        raise HTTPException(status_code=400, detail="Invalid password or email")
    if not user.password == existing_user.password:
        # TODO: Hash the password and compare with the hashed password in the database
        raise HTTPException(status_code=400, detail="Invalid password or email")

    access_token = create_access_token(data={"sub": str(existing_user.id), "email": existing_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
