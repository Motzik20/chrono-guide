from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG = None


class EnvConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
    )

    IS_LOCAL: bool = False


def get_config() -> EnvConfig:
    global _CONFIG
    if not _CONFIG:
        _CONFIG = EnvConfig()
    return _CONFIG


def is_local_env() -> bool:
    config = get_config()
    return config.IS_LOCAL


def create_local_config():
    global _CONFIG
    _CONFIG = EnvConfig(IS_LOCAL=True)
