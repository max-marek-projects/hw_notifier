"""Bot configuration."""

from enum import IntEnum, StrEnum
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from pathlib import Path

from aiogram.fsm.state import State, StatesGroup
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingLevels(IntEnum):
    """Allowed logging levels."""

    DEBUG = DEBUG
    INFO = INFO
    WARNING = WARNING
    ERROR = ERROR
    CRITICAL = CRITICAL


class Settings(BaseSettings):  # type: ignore[explicit-any]
    """Configuration from .env, environment and other constants.

    Attributes:
        model_config: configuration to parse variables from env file.
    """

    # env vars
    BOT_TOKEN: SecretStr = Field(..., alias="TOKEN", description="Token @BotFather")

    # constants
    POLL_INTERVAL: int = 30  # api poll interval
    REQUEST_TIMEOUT: int = 20  # api request timeout
    DB_PATH: Path = Path(__file__).resolve().parent / "hw.db"
    LOGS_PATH: Path = Path(__file__).resolve().parent / "logs"

    # logging
    LOGGER_LEVEL: LoggingLevels = LoggingLevels.INFO
    LOGGER_NAME: str = "HW-bot"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Buttons(StrEnum):
    """Button names."""

    NOTIFY_TEXT = "Notify on homework updates"
    STOP_TEXT = "Stop notifications"
    REPORT_TEXT = "Full report"
    REGISTER_TEXT = "Register using Yandex Oauth"
    HELP = "Help"


class States(StatesGroup):
    """Bot states.

    Attributes:
        waiting_for_token: state when bot waits for user to send him practicum access token.
    """

    waiting_for_token = State()


class Urls(StrEnum):
    """Urls used in chatbot."""

    OAUTH_URL = "https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a"
    PRACTICUM_ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"


class DateFormats(StrEnum):
    """Date formats used in telegram bot."""

    PRACTICUM = "%Y-%m-%dT%H:%M:%SZ"
    USER_FRIENDLY = "%d.%m.%Y %H:%M:%S"
    LOGS = "%Y-%m-%d %H.%M.%S.%f"


config = Settings()
