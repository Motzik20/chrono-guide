import icalendar
from caldav.collection import Calendar, Principal
from caldav.davclient import DAVClient
from sqlmodel import Session

from app.crud.calendar_connection_crud import get_calendar_connections_by_user_id
from app.crud.schedule_item_crud import sync_schedule_items_to_db
from app.models.calender_connections import CalendarConnection
from app.models.schedule_item import ScheduleItem
from app.schemas.schedule_item import ScheduleItemCreate


def _create_caldav_basic(calendar_connection: CalendarConnection) -> Principal:
    if calendar_connection.connection_type != "caldav_basic":
        raise ValueError(
            f"Unsupported connection type: {calendar_connection.connection_type}"
        )
    caldav_client: DAVClient = DAVClient(
        url=calendar_connection.calendar_url,
        username=calendar_connection.username,
        password=calendar_connection.secret,
    )

    return caldav_client.get_principal()


def _generate_uid(schedule_item: ScheduleItem) -> str:
    return f"{schedule_item.id}-{schedule_item.user_id}@chrono-guide.com"


def _generate_calender() -> icalendar.Calendar:
    calendar = icalendar.Calendar()
    calendar.add("prodid", "-//Chrono-Guide//EN")
    calendar.add("version", "2.0")
    return calendar


def _generate_event(schedule_item: ScheduleItem) -> icalendar.Event:
    event = icalendar.Event()
    event.add("uid", _generate_uid(schedule_item))
    event.add("summary", schedule_item.title)
    if schedule_item.description:
        event.add("description", schedule_item.description)
    event.add("dtstart", schedule_item.start_time)
    event.add("dtend", schedule_item.end_time)
    return event


def export_calendar_from_schedule_items(schedule_items: list[ScheduleItem]) -> bytes:
    calendar = _generate_calender()
    for schedule_item in schedule_items:
        event = _generate_event(schedule_item)
        calendar.add_component(event)
    return calendar.to_ical()


def create_clients(connections: list[CalendarConnection]) -> list[Principal]:
    # TODO: Expand this to more then just basic caldav connections in the future
    return [_create_caldav_basic(conn) for conn in connections]


def sync_calendars(user: int, session: Session) -> None:
    schedule_items: list[ScheduleItemCreate] = []
    connections: list[CalendarConnection] = get_calendar_connections_by_user_id(
        user_id=user, session=session
    )
    for connection in connections:
        client = _create_caldav_basic(connection)
        schedule_items.extend(
            get_schedule_items_for_principal(client, user, connection)
        )

    sync_schedule_items_to_db(schedule_items, user_id=user, session=session)


def get_schedule_items_for_principal(
    client: Principal, user_id: int, connection: CalendarConnection
) -> list[ScheduleItemCreate]:
    calendars: list[Calendar] = client.get_calendars()
    schedule_items: list[ScheduleItemCreate] = []
    for calendar in calendars:
        events = calendar.events()
        for event in events:
            ical_event = event.icalendar_component
            title = str(ical_event.get("summary"))
            description = str(ical_event.get("description", ""))
            start_time = ical_event.get("dtstart").dt
            end_time = ical_event.get("dtend").dt
            uid = ical_event.get("uid")
            schedule_item = ScheduleItemCreate(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                source="caldav",
                task_id=None,
                user_id=user_id,
                external_id=str(uid) if uid is not None else None,
                connection_id=connection.id,
            )
            schedule_items.append(schedule_item)
    return schedule_items


if __name__ == "__main__":
    # Example usage
    from app.core.db import get_db

    session = next(get_db())
    sync_calendars(user=1, session=session)
    session.commit()
