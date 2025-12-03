from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG: EnvConfig | None = None


class EnvConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
    )

    IS_LOCAL: bool = False


def get_config() -> EnvConfig:
    global _CONFIG
    if not _CONFIG:
        _CONFIG = EnvConfig()  # type: ignore
    assert _CONFIG is not None
    return _CONFIG


def is_local_env() -> bool:
    config = get_config()
    return config.IS_LOCAL


def create_local_config() -> None:
    global _CONFIG
    _CONFIG = EnvConfig(IS_LOCAL=True)  # type: ignore
