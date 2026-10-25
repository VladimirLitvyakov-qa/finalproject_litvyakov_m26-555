import tomllib
from typing import Self


class SettingsLoader:
    _instance: Self | None = None

    # Singleton через __new__: простой способ управлять созданием экземпляра.
    def __new__(cls) -> Self:

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        assert cls._instance is not None
        return cls._instance

    def __init__(self):

        if hasattr(self, "_settings"):
            return

        with open("pyproject.toml", "rb") as file:
            config = tomllib.load(file)

        self._settings = config["tool"]["valutatrade"]

    def get(self, key: str, default=None):
        """Получить настройку по ключу"""
        return self._settings.get(key, default)
