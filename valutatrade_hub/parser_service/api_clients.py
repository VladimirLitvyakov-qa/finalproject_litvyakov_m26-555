from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.core.utils import validate_amount
from valutatrade_hub.parser_service.config import ParserConfig

parser_config = ParserConfig
base_currency = parser_config.BASE_CURRENCY


class BaseApiClient(ABC):
    source: str

    @abstractmethod
    def fetch_rates(self) -> dict:
        pass


class CoinGeckoClient(BaseApiClient):
    source = "CoinGecko"

    def fetch_rates(self) -> dict:
        """
        Получает курсы фиатных валют из ExchangeRate-API

        :return: словарь с валютными парами и их числовыми курсами
        :raises ApiRequestError: при ошибке запроса или некорректном значении курса
        """
        crypto_id_map = parser_config.CRYPTO_ID_MAP
        params = {
            "ids": ",".join(crypto_id_map.values()),
            "vs_currencies": base_currency.lower(),
        }

        try:
            response = requests.get(
                url=parser_config.COINGECKO_URL,
                params=params,
                timeout=parser_config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as error:
            raise ApiRequestError(str(error)) from error

        rates = {}
        for code, name in crypto_id_map.items():
            rate_name = code + "_" + base_currency
            rate_value = data[name][base_currency.lower()]
            try:
                validate_amount(rate_value)
            except (TypeError, ValueError) as error:
                raise ApiRequestError(
                    f"Некорректный курс для {rate_name}: {rate_value!r}"
                ) from error

            rates[rate_name] = rate_value

        return rates


class ExchangeRateApiClient(BaseApiClient):
    source = "ExchangeRate-API"

    def fetch_rates(self) -> dict:
        """
        Получает курсы криптовалют из exchangerate

        :return: словарь с валютными парами и их числовыми курсами
        :raises ApiRequestError: при ошибке запроса или некорректном значении курса
        """
        exchangerate_url = parser_config.EXCHANGERATE_API_URL
        exchangerate_api_key = parser_config.EXCHANGERATE_API_KEY

        if not exchangerate_api_key:
            raise ApiRequestError(
                "Переменная окружения EXCHANGERATE_API_KEY не задана."
            )

        url = f"{exchangerate_url}/{exchangerate_api_key}/latest/{base_currency}"

        try:
            response = requests.get(url=url, timeout=parser_config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as error:
            raise ApiRequestError(str(error)) from error

        if data["result"] != "success":
            raise ApiRequestError(data["error-type"])

        rates = {}
        for currency_code in parser_config.FIAT_CURRENCIES:
            rate_name = currency_code + "_" + base_currency
            rate_value = data["conversion_rates"][currency_code]

            try:
                validate_amount(rate_value)
            except (TypeError, ValueError) as error:
                raise ApiRequestError(
                    f"Некорректный курс для {rate_name}: {rate_value!r}"
                ) from error

            rates[rate_name] = 1 / rate_value

        return rates
