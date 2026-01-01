from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models.schedule_item import ScheduleItem
from app.schemas.schedule_item import ScheduleItemCreate
from app.services.scheduling_service import ScheduleBlock


def get_user_schedule_items(
    user_id: int, session: Session, source: str | None = None
) -> list[ScheduleItem]:
    query = select(ScheduleItem).where(ScheduleItem.user_id == user_id)
    if source:
        query = query.where(ScheduleItem.source == source)
    return list(session.exec(query).all())


def create_schedule_items(
    schedule_items: list[ScheduleItemCreate], session: Session
) -> list[ScheduleItem]:
    schedule_item_models: list[ScheduleItem] = []
    for schedule_item in schedule_items:
        schedule_item_model: ScheduleItem = ScheduleItem.model_validate(schedule_item)
        schedule_item_models.append(schedule_item_model)
    session.add_all(schedule_item_models)
    session.flush()
    for schedule_item_model in schedule_item_models:
        session.refresh(schedule_item_model)
    return schedule_item_models


def get_schedule_item(schedule_item_id: int, session: Session) -> ScheduleItem:
    item = session.get(ScheduleItem, schedule_item_id)
    if item is None:
        raise NotFoundError(f"Schedule item with id {schedule_item_id} not found")
    return item


def create_schedule_items_from_blocks(
    schedule_blocks: list[ScheduleBlock], user_id: int, session: Session
) -> list[ScheduleItem]:
    """Convert schedule blocks to schedule items and save to database."""
    schedule_items: list[ScheduleItem] = []
    for block in schedule_blocks:
        schedule_item: ScheduleItem = ScheduleItem(
            user_id=user_id,
            task_id=block.task_id,
            start_time=block.start_time,
            end_time=block.end_time,
            source=block.source,
            title=block.title,
            description=block.description,
        )
        schedule_items.append(schedule_item)
        session.add(schedule_item)

    session.commit()
    for item in schedule_items:
        session.refresh(item)

    return schedule_items
