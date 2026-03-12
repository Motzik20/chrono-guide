from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models.schedule_item import ScheduleItem
from app.schemas.schedule_item import ScheduleItemCreate
from app.services.scheduling_types import ScheduleBlock


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

    session.flush()
    for item in schedule_items:
        session.refresh(item)

    return schedule_items


def sync_schedule_items_to_db(
    schedule_items: list[ScheduleItemCreate], user_id: int, session: Session
) -> list[ScheduleItem]:
    """Sync schedule items for a user. This will create new items, update existing ones, and delete items that are no longer present."""
    existing_items = get_user_schedule_items(user_id=user_id, session=session)
    existing_items_map: dict[tuple[str, str, int], ScheduleItem] = {
        (item.source, item.external_id, item.connection_id): item
        for item in existing_items
        if item.external_id is not None and item.connection_id is not None
    }

    new_items: list[ScheduleItem] = []
    for item in schedule_items:
        if (
            item.external_id is None
            or item.connection_id is None
            or item.source is None
        ):
            continue
        key: tuple[str, str, int] = (item.source, item.external_id, item.connection_id)
        if key in existing_items_map:
            # Update existing item
            existing_item = existing_items_map[key]
            existing_item.start_time = item.start_time
            existing_item.end_time = item.end_time
            existing_item.title = item.title
            existing_item.description = item.description
            new_items.append(existing_item)
            del existing_items_map[key]
        else:
            # Create new item
            new_item = ScheduleItem(
                user_id=user_id,
                task_id=item.task_id,
                start_time=item.start_time,
                end_time=item.end_time,
                source=item.source,
                title=item.title,
                description=item.description,
                external_id=item.external_id,
                connection_id=item.connection_id,
            )
            session.add(new_item)
            new_items.append(new_item)

    # Delete items that are no longer present
    for remaining_item in existing_items_map.values():
        session.delete(remaining_item)

    session.flush()
    for item in new_items:
        session.refresh(item)

    return new_items
