from typing import TypedDict


class SettingMetadata(TypedDict):
    type: str
    description: str
    option_type: str | None
    options: list[dict[str, str]] | str | None


DEFAULT_USER_SETTINGS: dict[str, str] = {
    "timezone": "UTC",
    "language": "en",
    "allow_task_splitting": "true",
}

METADATA_SETTINGS: dict[str, SettingMetadata] = {
    "timezone": {
        "type": "string",
        "description": "The timezone of the user",
        "option_type": "dynamic",
        "options": "get_timezones_options",
    },
    "language": {
        "type": "string",
        "description": "The language of the user",
        "option_type": "static",
        "options": [
            {"value": "en", "label": "English"},
            {"value": "de", "label": "German"},
            {"value": "es", "label": "Spanish"},
            {"value": "fr", "label": "French"},
            {"value": "it", "label": "Italian"},
            {"value": "pt", "label": "Portuguese"},
        ],
    },
    "allow_task_splitting": {
        "type": "boolean",
        "description": "Whether to allow task splitting",
        "option_type": None,
        "options": None,
    },
}
