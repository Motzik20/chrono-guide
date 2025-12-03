from fastapi import APIRouter, Body

from app.schemas.schedule_requests import ScheduleCommitRequest, ScheduleGenerateRequest

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/generate")
async def generate_schedule(schedule: ScheduleGenerateRequest = Body(...)) -> dict[str, str]:  # noqa: ARG001
    return {"Not implemented": "Generating schedules is not implemented"}


@router.post("/commit")
async def commit_schedule(schedule: ScheduleCommitRequest = Body(...)) -> dict[str, str]:  # noqa: ARG001
    return {"Not implemented": "Committing schedules is not implemented"}
