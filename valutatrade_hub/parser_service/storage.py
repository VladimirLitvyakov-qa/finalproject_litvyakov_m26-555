import os
from datetime import datetime

from valutatrade_hub.core.utils import load_json, save_json
from valutatrade_hub.parser_service.config import ParserConfig

parser_config = ParserConfig


class RatesStorage:
    def __init__(self):
        self._history_path = parser_config.HISTORY_FILE_PATH
        self._rates_path = parser_config.RATES_FILE_PATH

    def load_history(self) -> list[dict]:
        """Загружает и возвращает историю полученных курсов"""
        history_rates = load_json(self._history_path, [])

        if not isinstance(history_rates, list):
            raise ValueError(
                "Файл с историей полученных курсов должен содержать список."
            )

        return history_rates

    def save_history(self, history: list[dict]) -> None:
        """Сохраняет историю полученных курсов"""
        temp_file = f"{self._history_path}.tmp"
        save_json(temp_file, history)

        os.replace(temp_file, self._history_path)

    def append_history(self, records: list[dict]) -> None:
        """Добавляет новые изменения в историю, пропуская
        записи с уже существующими id."""
        history = self.load_history()
        existing_ids = {ex_id["id"] for ex_id in history}

        for new in records:
            if new["id"] not in existing_ids:
                existing_ids.add(new["id"])
                history.append(new)

        self.save_history(history)

    def load_rates(self) -> dict:
        """Загружает и возвращает актуальные курсы валют"""
        rates = load_json(self._rates_path, {"pairs": {}, "last_refresh": None})

        if not isinstance(rates, dict):
            raise ValueError("Файл с курсами валют должен содержать словарь.")

        return rates

    def save_rates(self, rates: dict) -> None:
        """Сохраняет актуальные курсы валют"""
        temp_file = f"{self._rates_path}.tmp"
        save_json(temp_file, rates)

        os.replace(temp_file, self._rates_path)

    def update_rates(self, new_rates: dict) -> None:
        """Обновляет кеш, добавляя новые пары и заменяя устаревшие записи."""
        rates = self.load_rates()

        for currency_pair, new_rate in new_rates["pairs"].items():
            current_rate = rates["pairs"].get(currency_pair)

            if current_rate:
                current_time = datetime.fromisoformat(current_rate["updated_at"])
                new_time = datetime.fromisoformat(new_rate["updated_at"])

                if new_time > current_time:
                    rates["pairs"][currency_pair] = new_rate

            else:
                rates["pairs"][currency_pair] = new_rate

        if rates["last_refresh"] is None:
            rates["last_refresh"] = new_rates["last_refresh"]
        else:
            current_refresh = datetime.fromisoformat(rates["last_refresh"])
            new_refresh = datetime.fromisoformat(new_rates["last_refresh"])

            if new_refresh > current_refresh:
                rates["last_refresh"] = new_rates["last_refresh"]

        self.save_rates(rates)
