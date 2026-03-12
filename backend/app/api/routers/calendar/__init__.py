from fastapi import APIRouter
from .connections import router as connections_router

router: APIRouter = APIRouter(prefix="/calendar", tags=["calendar"])

router.include_router(connections_router)