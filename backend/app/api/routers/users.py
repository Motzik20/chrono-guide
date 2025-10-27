from fastapi import APIRouter, Body

from app.schemas.user import UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/registration")
async def get_registration(user: UserCreate = Body(...)):
    pass
