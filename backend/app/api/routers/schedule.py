from fastapi import APIRouter, Body, Depends, Response
from sqlmodel import Session

from app.core.auth import get_current_user_id
from app.core.db import get_db
from app.core.timezone import get_user_timezone, now_utc
from app.crud.availability_crud import get_user_availability
from app.crud.schedule_item_crud import create_schedule_items, get_user_schedule_items
from app.crud.task_crud import (
    get_tasks_by_ids,
    get_unscheduled_tasks,
    update_tasks_scheduled_at,
)
from app.models.availability import WeeklyAvailability
from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.schemas.schedule_item import ScheduleItemCreate
from app.schemas.schedule_requests import ScheduleGenerateRequest
from app.services.ical_service import export_calendar_from_schedule_items
from app.services.scheduling_service import (
    SchedulingResponse,
    schedule_blocks_to_schedule_items,
    schedule_tasks,
)

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/export")
async def export_schedule(
    user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)
) -> Response:
    schedule_items: list[ScheduleItem] = get_user_schedule_items(
        user_id, session, source="task"
    )
    ical_bytes: bytes = export_calendar_from_schedule_items(schedule_items)
    return Response(
        content=ical_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=schedule_{user_id}.ics"},
    )


@router.get("/items")
async def get_schedule_items(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    source: str | None = None,
) -> list[ScheduleItem]:
    return get_user_schedule_items(user_id, session, source)


@router.post("/generate/selected")
async def generate_schedule(
    generate_schedule_request: ScheduleGenerateRequest = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> SchedulingResponse:
    timezone: str = get_user_timezone(session, user_id)
    tasks: list[Task] = get_tasks_by_ids(
        generate_schedule_request.task_ids, user_id, session
    )
    schedule_items: list[ScheduleItem] = get_user_schedule_items(user_id, session)
    availability: WeeklyAvailability = get_user_availability(user_id, session)
    response: SchedulingResponse = schedule_tasks(
        tasks, schedule_items, availability, timezone
    )
    schedule_items_to_create: list[ScheduleItemCreate] = (
        schedule_blocks_to_schedule_items(response.schedule_blocks, user_id)
    )

    create_schedule_items(schedule_items_to_create, session)
    update_tasks_scheduled_at(
        [block.task_id for block in response.schedule_blocks],
        now_utc(),
        user_id,
        session,
    )
    return response


@router.post("/generate/all")
async def generate_schedule_all(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> SchedulingResponse:
    timezone: str = get_user_timezone(session, user_id)
    tasks: list[Task] = get_unscheduled_tasks(user_id, session)
    schedule_items: list[ScheduleItem] = get_user_schedule_items(user_id, session)
    availability: WeeklyAvailability = get_user_availability(user_id, session)
    response: SchedulingResponse = schedule_tasks(
        tasks, schedule_items, availability, timezone
    )
    schedule_items_to_create: list[ScheduleItemCreate] = (
        schedule_blocks_to_schedule_items(response.schedule_blocks, user_id)
    )
    create_schedule_items(schedule_items_to_create, session)
    update_tasks_scheduled_at(
        [block.task_id for block in response.schedule_blocks],
        now_utc(),
        user_id,
        session,
    )
    return response


# TODO: When calender View is implemented, we want following endpoints in order to stage a schedule and commit/discard it:
# TODO: 1. /schedule/generate (currently saves but later should show a preview)
# TODO: 2. /schedule/comiit (commits the schedule, so actually saves the schedule)
