class InsufficientFundsError(Exception):
    """Недостаточно средств на балансе"""

    def __init__(self, available: float, required: float, code: str) -> None:
        message = (
            f"Недостаточно средств: доступно {available} {code}, "
            f"требуется {required} {code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Неизвестная валюта"""

    def __init__(self, code: str) -> None:
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """Ошибка API запроса"""

    def __init__(self, reason: str) -> None:
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)
