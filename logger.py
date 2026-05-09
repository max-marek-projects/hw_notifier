"""Telegram bot logger."""

import logging
from datetime import datetime

from config import DateFormats, config


def _get_logger() -> logging.Logger:
    """Get logger for current project.

    Returns:
        Logger for current project.
    """
    logger = logging.getLogger(config.LOGGER_NAME)
    logger.setLevel(config.LOGGER_LEVEL)
    # format
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(threadName)-12s - %(levelname)-8s - %(message)s")
    # file
    config.LOGS_PATH.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(config.LOGS_PATH / f"{datetime.now().strftime(DateFormats.LOGS)}.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(config.LOGGER_LEVEL)
    logger.addHandler(file_handler)
    # console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(config.LOGGER_LEVEL)
    logger.addHandler(console_handler)
    return logger


logger = _get_logger()
