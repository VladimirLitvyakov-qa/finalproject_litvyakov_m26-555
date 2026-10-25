from typing import Self

from valutatrade_hub.core.utils import load_json, save_json
from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    _instance: Self | None = None

    def __new__(cls) -> Self:

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        assert cls._instance is not None
        return cls._instance

    def __init__(self):

        if hasattr(self, "_settings"):
            return

        self._settings = SettingsLoader()

    def load_users(self) -> list[dict]:
        """Загружает и возвращает список пользователей"""
        path = self._settings.get("users_path")

        users = load_json(path, [])

        if not isinstance(users, list):
            raise ValueError("Файл пользователей должен содержать список.")

        return users

    def save_users(self, users: list[dict]) -> None:
        """Сохраняет список пользователей"""
        path = self._settings.get("users_path")
        save_json(path, users)

    def load_portfolios(self) -> list[dict]:
        """Загружает и возвращает список портфелей"""
        path = self._settings.get("portfolios_path")

        portfolios = load_json(path, [])

        if not isinstance(portfolios, list):
            raise ValueError("Файл портфелей должен содержать список.")

        return portfolios

    def save_portfolios(self, portfolios: list[dict]) -> None:
        """Сохраняет список портфелей"""
        path = self._settings.get("portfolios_path")
        save_json(path, portfolios)

    def load_rates(self) -> dict:
        """Загружает и возвращает курсы валют"""
        path = self._settings.get("rates_path")

        rates = load_json(path, {})

        if not isinstance(rates, dict):
            raise ValueError("Файл курсов должен содержать словарь.")

        return rates

    def save_rates(self, rates: dict) -> None:
        """Сохраняет курсы валют"""
        path = self._settings.get("rates_path")
        save_json(path, rates)
