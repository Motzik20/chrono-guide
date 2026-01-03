import datetime as dt
from typing import Any

import pytz  # type: ignore[import-untyped]
from sqlmodel import Session, select


def ensure_utc(dt_obj: dt.datetime | None) -> dt.datetime | None:
    """
    Ensure a datetime is timezone-aware and in UTC.
    If naive, assumes UTC. If timezone-aware, converts to UTC.
    """
    if dt_obj is None:
        return None

    if dt_obj.tzinfo is None:
        # Naive datetime - assume UTC
        return dt_obj.replace(tzinfo=dt.timezone.utc)

    # Timezone-aware datetime - convert to UTC
    return dt_obj.astimezone(dt.timezone.utc)


def convert_to_user_timezone(
    utc_dt: dt.datetime | None, user_timezone: str
) -> dt.datetime | None:
    """
    Convert a UTC datetime to user's timezone.
    """
    if utc_dt is None:
        return None

    if utc_dt.tzinfo is None:
        # If somehow naive, assume UTC
        utc_dt = utc_dt.replace(tzinfo=dt.timezone.utc)

    try:
        user_tz = pytz.timezone(user_timezone)
        return utc_dt.astimezone(user_tz)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback to UTC if timezone is invalid
        return utc_dt


def now_utc() -> dt.datetime:
    """Get current time in UTC."""
    return dt.datetime.now(dt.timezone.utc)


def parse_user_datetime(user_dt: dt.datetime, user_timezone: str) -> dt.datetime:
    """
    Parse a datetime from user's timezone and convert to UTC for storage.
    """
    if user_dt.tzinfo is None:
        # If user provided naive datetime, assume it's in their timezone
        try:
            user_tz = pytz.timezone(user_timezone)
            user_dt = user_tz.localize(user_dt)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fallback to UTC
            user_dt = user_dt.replace(tzinfo=dt.timezone.utc)

    # Convert to UTC for storage
    return user_dt.astimezone(dt.timezone.utc)


def get_user_timezone(session: Session, user_id: int) -> str:
    """
    Get user's timezone from settings, default to UTC.
    """
    from app.models.user_setting import UserSetting

    setting: UserSetting | None = session.exec(
        select(UserSetting)
        .where(UserSetting.user_id == user_id)
        .where(UserSetting.key == "timezone")
    ).first()

    return setting.value if setting else "UTC"


def convert_model_datetimes_to_utc(model_data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert all datetime fields in a model to UTC using model_validator.
    """
    datetime_fields = ["created_at", "updated_at", "deadline", "start_time", "end_time", "committed_at"]

    for field in datetime_fields:
        if field in model_data and model_data[field] is not None:
            model_data[field] = ensure_utc(model_data[field])

    return model_data


def get_next_half_hour(now: dt.datetime) -> dt.datetime:
    """Get the next half-hour mark from the current time."""
    # Round up to the next half-hour
    minutes = now.minute
    if minutes < 30:
        # Round to next 30-minute mark
        rounded_minutes = 30
    else:
        # Round to next hour (00 minutes)
        rounded_minutes = 0
        now = now + dt.timedelta(hours=1)

    return now.replace(minute=rounded_minutes, second=0, microsecond=0)


def get_next_weekday(current_datetime: dt.datetime, weekday: int = 0) -> dt.datetime:
    current_day_of_week: int = current_datetime.weekday()
    days_ahead = (weekday - current_day_of_week - 1) % 7 + 1
    next_weekday = current_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + dt.timedelta(days_ahead)

    return next_weekday
