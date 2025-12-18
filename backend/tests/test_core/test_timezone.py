import datetime as dt
from unittest.mock import Mock

from app.core.timezone import (
    convert_model_datetimes_to_utc,
    convert_to_user_timezone,
    ensure_utc,
    get_next_half_hour,
    get_next_weekday,
    get_user_timezone,
    now_utc,
    parse_user_datetime,
)
from app.models.user_setting import UserSetting
from app.schemas.availability import DayOfWeek


class TestEnsureUTC:
    """Test the ensure_utc function."""

    def test_ensure_utc_with_none(self):
        """Test ensure_utc with None input."""
        assert ensure_utc(None) is None

    def test_ensure_utc_with_naive_datetime(self):
        """Test ensure_utc with naive datetime (assumes UTC)."""
        naive_dt = dt.datetime(2024, 1, 1, 12, 0, 0)
        result = ensure_utc(naive_dt)

        assert result is not None
        assert result.tzinfo == dt.timezone.utc
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 0
        assert result.second == 0

    def test_ensure_utc_with_utc_datetime(self):
        """Test ensure_utc with already UTC datetime."""
        utc_dt = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = ensure_utc(utc_dt)

        assert result is not None
        assert result.tzinfo == dt.timezone.utc
        assert result == utc_dt

    def test_ensure_utc_with_other_timezone(self):
        """Test ensure_utc with timezone-aware datetime in different timezone."""
        # Create a datetime in EST (UTC-5)
        est_tz = dt.timezone(dt.timedelta(hours=-5))
        est_dt = dt.datetime(2024, 1, 1, 7, 0, 0, tzinfo=est_tz)
        result = ensure_utc(est_dt)

        assert result is not None
        assert result.tzinfo == dt.timezone.utc
        assert result.hour == 12
        assert result.minute == 0


class TestConvertToUserTimezone:
    """Test the convert_to_user_timezone function."""

    def test_convert_to_user_timezone_with_none(self):
        """Test convert_to_user_timezone with None input."""
        assert convert_to_user_timezone(None, "America/New_York") is None

    def test_convert_to_user_timezone_with_utc(self):
        """Test convert_to_user_timezone with UTC datetime."""
        utc_dt = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = convert_to_user_timezone(utc_dt, "America/New_York")

        assert result is not None
        assert result.hour == 7
        assert result.minute == 0

    def test_convert_to_user_timezone_with_naive_datetime(self):
        """Test convert_to_user_timezone with naive datetime (assumes UTC)."""
        naive_dt = dt.datetime(2024, 1, 1, 12, 0, 0)
        result = convert_to_user_timezone(naive_dt, "America/New_York")

        assert result is not None
        assert result.hour == 7
        assert result.minute == 0

    def test_convert_to_user_timezone_invalid_timezone(self):
        """Test convert_to_user_timezone with invalid timezone (fallback to UTC)."""
        utc_dt = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = convert_to_user_timezone(utc_dt, "Invalid/Timezone")

        assert result == utc_dt


class TestNowUTC:
    """Test the now_utc function."""

    def test_now_utc_returns_utc(self):
        """Test that now_utc returns a UTC datetime."""
        result = now_utc()

        assert result.tzinfo == dt.timezone.utc
        assert isinstance(result, dt.datetime)

    def test_now_utc_is_recent(self):
        """Test that now_utc returns a recent datetime."""
        result = now_utc()
        now = dt.datetime.now(dt.timezone.utc)

        time_diff = abs((now - result).total_seconds())
        assert time_diff < 1


class TestParseUserDatetime:
    """Test the parse_user_datetime function."""

    def test_parse_user_datetime_naive(self):
        """Test parse_user_datetime with naive datetime."""
        naive_dt = dt.datetime(2024, 1, 1, 12, 0, 0)
        result = parse_user_datetime(naive_dt, "America/New_York")

        assert result.tzinfo == dt.timezone.utc
        assert result.hour == 17
        assert result.minute == 0

    def test_parse_user_datetime_timezone_aware(self):
        """Test parse_user_datetime with timezone-aware datetime."""
        est_tz = dt.timezone(dt.timedelta(hours=-5))
        est_dt = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=est_tz)
        result = parse_user_datetime(est_dt, "America/New_York")

        assert result.tzinfo == dt.timezone.utc
        assert result.hour == 17
        assert result.minute == 0

    def test_parse_user_datetime_invalid_timezone(self):
        """Test parse_user_datetime with invalid timezone (fallback to UTC)."""
        naive_dt = dt.datetime(2024, 1, 1, 12, 0, 0)
        result = parse_user_datetime(naive_dt, "Invalid/Timezone")

        assert result.tzinfo == dt.timezone.utc
        assert result.hour == 12
        assert result.minute == 0


class TestGetUserTimezone:
    """Test the get_user_timezone function."""

    def test_get_user_timezone_with_setting(self):
        """Test get_user_timezone when user has timezone setting."""
        mock_session = Mock()
        mock_setting: UserSetting = UserSetting(user_id=1, key="timezone", value="America/New_York")

        mock_result = Mock()
        mock_result.first.return_value = mock_setting
        mock_session.exec.return_value = mock_result

        result: str = get_user_timezone(mock_session, 1)

        assert result == "America/New_York"

    def test_get_user_timezone_without_setting(self):
        """Test get_user_timezone when user has no timezone setting (default to UTC)."""
        mock_session = Mock()
        mock_session.exec.return_value.first.return_value = None

        result: str= get_user_timezone(mock_session, 1)

        assert result == "UTC"


class TestConvertModelDatetimesToUTC:
    """Test the convert_model_datetimes_to_utc function."""

    def test_convert_model_datetimes_to_utc_with_datetime_fields(self):
        """Test convert_model_datetimes_to_utc with datetime fields."""
        model_data = {
            "id": 1,
            "title": "Test",
            "created_at": dt.datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": dt.datetime(2024, 1, 1, 13, 0, 0),
            "deadline": dt.datetime(2024, 1, 2, 14, 0, 0),
        }

        result = convert_model_datetimes_to_utc(model_data)

        assert result["id"] == 1
        assert result["title"] == "Test"
        assert result["created_at"].tzinfo == dt.timezone.utc
        assert result["updated_at"].tzinfo == dt.timezone.utc
        assert result["deadline"].tzinfo == dt.timezone.utc

    def test_convert_model_datetimes_to_utc_with_none_values(self):
        """Test convert_model_datetimes_to_utc with None datetime values."""
        model_data = {
            "id": 1,
            "title": "Test",
            "created_at": None,
            "deadline": None,
        }

        result = convert_model_datetimes_to_utc(model_data)

        assert result["id"] == 1
        assert result["title"] == "Test"
        assert result["created_at"] is None
        assert result["deadline"] is None

    def test_convert_model_datetimes_to_utc_with_timezone_aware(self):
        """Test convert_model_datetimes_to_utc with timezone-aware datetimes."""
        est_tz = dt.timezone(dt.timedelta(hours=-5))
        model_data = {
            "id": 1,
            "created_at": dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=est_tz),
        }

        result = convert_model_datetimes_to_utc(model_data)

        assert result["created_at"].tzinfo == dt.timezone.utc
        assert result["created_at"].hour == 17


class TestGetNextHalfHour:
    """Test the get_next_half_hour function."""

    def test_get_next_half_hour_before_30_minutes(self):
        """Test get_next_half_hour when current time is before 30 minutes."""
        current_time = dt.datetime(2024, 1, 1, 12, 15, 30, tzinfo=dt.timezone.utc)
        result = get_next_half_hour(current_time)

        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_next_half_hour_after_30_minutes(self):
        """Test get_next_half_hour when current time is after 30 minutes."""
        current_time = dt.datetime(2024, 1, 1, 12, 45, 30, tzinfo=dt.timezone.utc)
        result = get_next_half_hour(current_time)

        assert result.hour == 13
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_next_half_hour_exactly_30_minutes(self):
        """Test get_next_half_hour when current time is exactly 30 minutes."""
        current_time = dt.datetime(2024, 1, 1, 12, 30, 0, tzinfo=dt.timezone.utc)
        result = get_next_half_hour(current_time)

        assert result.hour == 13
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_next_half_hour_exactly_hour(self):
        """Test get_next_half_hour when current time is exactly on the hour."""
        current_time = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = get_next_half_hour(current_time)

        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 0
        assert result.microsecond == 0


class TestGetNextWeekday:
    """Test the get_next_weekday function."""

    def test_get_next_weekday_monday_to_tuesday(self):
        """Test get_next_weekday from Monday to Tuesday."""
        # Monday (weekday=0)
        monday = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = get_next_weekday(monday, weekday=1)  # Tuesday

        assert result.weekday() == 1
        assert result.day == 2
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_next_weekday_friday_to_monday(self):
        """Test get_next_weekday from Friday to Monday (next week)."""
        friday = dt.datetime(2024, 1, 5, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = get_next_weekday(friday, weekday=0)  # Monday

        assert result.weekday() == 0  # Monday
        assert result.day == 8
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_next_weekday_same_day(self):
        """Test get_next_weekday when requesting the same day."""
        monday = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = get_next_weekday(monday, weekday=0)

        assert result.weekday() == 0
        assert result.day == 8
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_next_weekday_default_weekday(self):
        """Test get_next_weekday with default weekday (Monday)."""
        wednesday = dt.datetime(2024, 1, 3, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = get_next_weekday(wednesday)

        assert result.weekday() == 0
        assert result.day == 8
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_next_monday(self):
        monday: dt.datetime = dt.datetime(
            year=2025, month=9, day=1, hour=12, tzinfo=dt.timezone.utc
        )
        next_monday: dt.datetime = get_next_weekday(monday)
        assert next_monday.day == 8
        assert next_monday.month == 9
        assert next_monday.year == 2025
        assert next_monday.hour == 0

        sunday: dt.datetime = dt.datetime(
            year=2025, month=9, day=7, hour=12, tzinfo=dt.timezone.utc
        )
        next_monday_from_sunday = get_next_weekday(sunday)
        assert next_monday == next_monday_from_sunday

    def test_get_next_wednesday(self):
        thursday: dt.datetime = dt.datetime(
            year=2025, month=9, day=4, hour=12, tzinfo=dt.timezone.utc
        )
        next_wednesday: dt.datetime = get_next_weekday(thursday, DayOfWeek.WED)
        assert next_wednesday.day == 10
        assert next_wednesday.month == 9
        assert next_wednesday.year == 2025
        assert next_wednesday.hour == 0

        sunday: dt.datetime = dt.datetime(
            year=2025, month=9, day=7, hour=12, tzinfo=dt.timezone.utc
        )
        next_monday_from_sunday = get_next_weekday(sunday, DayOfWeek.WED)
        assert next_wednesday == next_monday_from_sunday


class TestTimezoneIntegration:
    """Integration tests for timezone functions."""

    def test_full_timezone_conversion_workflow(self):
        """Test the complete workflow of timezone conversion."""
        user_timezone = "America/New_York"
        user_datetime = dt.datetime(2024, 1, 1, 14, 0, 0)

        utc_datetime = parse_user_datetime(user_datetime, user_timezone)
        assert utc_datetime is not None
        assert utc_datetime.tzinfo == dt.timezone.utc
        assert utc_datetime.hour == 19

        display_datetime = convert_to_user_timezone(utc_datetime, user_timezone)
        assert display_datetime is not None
        assert display_datetime.hour == 14

    def test_ensure_utc_with_mixed_timezones(self):
        """Test ensure_utc with various timezone scenarios."""
        naive_dt = dt.datetime(2024, 1, 1, 12, 0, 0)
        utc_naive = ensure_utc(naive_dt)
        assert utc_naive is not None
        assert utc_naive.tzinfo == dt.timezone.utc

        utc_dt = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        utc_result = ensure_utc(utc_dt)
        assert utc_result is not None
        assert utc_result == utc_dt

        est_tz = dt.timezone(dt.timedelta(hours=-5))
        est_dt = dt.datetime(2024, 1, 1, 7, 0, 0, tzinfo=est_tz)
        utc_est = ensure_utc(est_dt)
        assert utc_est is not None
        assert utc_est.tzinfo == dt.timezone.utc
        assert utc_est.hour == 12
