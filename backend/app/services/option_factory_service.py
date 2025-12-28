import pytz


def get_timezones_options() -> list[dict[str, str]]:
    return [
        {"value": tz, "label": tz.replace("/", " ")} for tz in pytz.common_timezones
    ]


OPTION_FACTORIES = {
    "get_timezones_options": get_timezones_options,
}
