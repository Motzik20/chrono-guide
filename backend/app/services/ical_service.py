import icalendar

from app.models.schedule_item import ScheduleItem


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
