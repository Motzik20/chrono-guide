from fastapi import APIRouter, Body

from app.schemas.schedule_requests import ScheduleCommitRequest, ScheduleGenerateRequest

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/generate")
async def generate_schedule(schedule: ScheduleGenerateRequest = Body(...)):
    pass


@router.post("/commit")
async def commit_schedule(schedule: ScheduleCommitRequest = Body(...)):
    pass
