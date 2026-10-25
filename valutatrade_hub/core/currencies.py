from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str) -> None:
        if not isinstance(name, str):
            raise TypeError(f"name must be str, but got {type(name).__name__}")
        if not name:
            raise ValueError("name не может быть пустым")

        if not isinstance(code, str):
            raise TypeError(f"code must be str, but got {type(code).__name__}")
        if not code:
            raise ValueError("code не может быть пустым")
        if len(code) < 2 or len(code) > 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов.")
        if " " in code:
            raise ValueError("Код валюты не должен содержать пробелы")

        code = code.upper()

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        pass


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        """Получить информацию о валюте."""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float) -> None:
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        """Получить информацию о крипто-валюте."""
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


CURRENCIES = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("EURO", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 3.0e11),
}


def get_currency(code: str) -> Currency:
    """
    Получить валюту

    :param code: код валюты
    :return: объект Currency
    :raises TypeError: если code не является строкой
    :raises ValueError: если code пустой
    :raises CurrencyNotFoundError: если валюта отсутствует в реестре
    """
    if not isinstance(code, str):
        raise TypeError(f"code must be str, but got {type(code).__name__}")

    if not code:
        raise ValueError("code не может быть пустым")

    code = code.upper()

    try:
        currency = CURRENCIES[code]
    except KeyError:
        raise CurrencyNotFoundError(code)

    return currency
