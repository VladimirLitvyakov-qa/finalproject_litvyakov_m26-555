import logging
from datetime import datetime, timezone

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.storage import RatesStorage

logger = logging.getLogger("valutatrade_hub")


class RatesUpdater:
    def __init__(self, clients: list[BaseApiClient], storage: RatesStorage) -> None:
        self._clients = clients
        self._storage = storage

    def run_update(self) -> dict:
        """Получает курсы от источников, сохраняет кеш и историю,
        возвращает итог обновления."""
        all_rates = {}
        failed_sources = []

        logger.info("Начало обновления курсов")
        for client in self._clients:
            updated_at = datetime.now(timezone.utc).isoformat()

            try:
                rates = client.fetch_rates()
                logger.info(f"{client.source}: получено курсов — {len(rates)}")
            except ApiRequestError as error:
                logger.error(f"{client.source}: не удалось получить курсы: {error}")
                failed_sources.append(client.source)
                continue

            for rate, amount in rates.items():
                data = {
                    "rate": amount,
                    "updated_at": updated_at,
                    "source": client.source,
                }

                all_rates[rate] = data

        if not all_rates:
            raise ApiRequestError("Не удалось получить курсы")

        cache_data = {
            "pairs": all_rates,
            "last_refresh": datetime.now(timezone.utc).isoformat(),
        }

        self._storage.update_rates(cache_data)

        history_records = []

        for currency_pair, values in all_rates.items():
            from_currency, to_currency = currency_pair.split("_", 1)
            pair_id = f"{currency_pair}_{values['updated_at']}"

            record = {
                "id": pair_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": values["rate"],
                "timestamp": values["updated_at"],
                "source": values["source"],
            }

            history_records.append(record)

        self._storage.append_history(history_records)
        logger.info(f"Обновление завершено: сохранено курсов — {len(all_rates)}")

        return {
            "updated_count": len(all_rates),
            "last_refresh": cache_data["last_refresh"],
            "failed_sources": failed_sources,
        }
