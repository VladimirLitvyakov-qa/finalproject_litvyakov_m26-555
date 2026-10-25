import logging
import os
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> None:
    """Настраивает запись логов в файл с ротацией"""
    settings = SettingsLoader()

    log_path = settings.get("log_path")
    log_level = settings.get("log_level")

    if not isinstance(log_path, str):
        raise TypeError("Настройка log_path должна быть строкой.")

    directory = os.path.dirname(log_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    logger = logging.getLogger("valutatrade_hub")

    if logger.handlers:
        return

    logger.setLevel(log_level)

    handler = RotatingFileHandler(
        filename=log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )

    formatter = logging.Formatter(
        fmt="%(levelname)s %(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
