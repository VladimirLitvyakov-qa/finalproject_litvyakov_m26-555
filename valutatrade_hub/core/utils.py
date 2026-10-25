import json
import os
from datetime import datetime

from valutatrade_hub.core.models import EXCHANGE_RATES, Portfolio, User, Wallet


def load_json(path: str, default: list | dict) -> list | dict:
    """
    Читает данные из JSON-файла

    :param path: путь до JSON-файла
    :param default: значение, возвращаемое при отсутствии файла
    :return: список или словарь из файла либо переданный default
    :raises ValueError: если файл содержит некорректный JSON
    """
    try:
        with open(path, encoding="UTF-8") as file:
            result = json.load(file)
    except FileNotFoundError:
        result = default
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in file.")

    return result


def save_json(path: str, data: list | dict) -> None:
    """
    Сохраняет данные в JSON-файл

    :param path: путь до JSON-файла
    :param data: список или словарь для сохранения
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="UTF-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def user_from_dict(data: dict) -> User:
    """
    Создает пользователя из словаря

    :param data: словарь
    :return: объект User
    """
    if not isinstance(data, dict):
        raise TypeError(f"data must be dict, but got {type(data).__name__}")

    user_id = data["user_id"]
    username = data["username"]
    hashed_password = data["hashed_password"]
    salt = data["salt"]
    registration_date = datetime.fromisoformat(data["registration_date"])

    return User(user_id, username, hashed_password, salt, registration_date)


def user_to_dict(user: User) -> dict:
    """
    Преобразовывает из объекта пользователя в словарь

    :param user: объект User
    :return: словарь с данными пользователя
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    user_id = user.user_id
    username = user.username
    hashed_password = user.hashed_password
    salt = user.salt
    registration_date = user.registration_date.isoformat()

    return {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": registration_date,
    }


def portfolio_to_dict(portfolio: Portfolio) -> dict:
    """
    Преобразовывает из объекта портфеля в словарь

    :param portfolio: объект Portfolio
    :return: словарь с портфелем пользователя
    """
    if not isinstance(portfolio, Portfolio):
        raise TypeError(
            f"portfolio must be Portfolio, but got {type(portfolio).__name__}"
        )

    user_id = portfolio.user_id
    wallets = {}

    for code, wallet in portfolio.wallets.items():
        wallets[code] = {"balance": wallet.balance}

    return {"user_id": user_id, "wallets": wallets}


def portfolio_from_dict(data: dict, user: User) -> Portfolio:
    """
    Создает портфель пользователя из словаря

    :param data: словарь
    :param user: объект User
    :return: объект Portfolio
    """
    if not isinstance(data, dict):
        raise TypeError(f"data must be dict, but got {type(data).__name__}")

    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    if data["user_id"] != user.user_id:
        raise ValueError("Портфель принадлежит другому пользователю")

    wallets = {}
    for code, wallet in data["wallets"].items():
        wallets[code] = Wallet(code, wallet["balance"])

    return Portfolio(user, wallets)


def validate_currency_code(currency_code: str) -> str:
    """
    Валидирует код валюты

    :param currency_code: код валюты
    :return: код валюты в верхнем регистре
    """
    if not isinstance(currency_code, str):
        raise TypeError(
            f"currency_code must be str, but got {type(currency_code).__name__}"
        )

    if not currency_code:
        raise ValueError("Код валюты не может быть пустой.")

    return currency_code.upper()


def get_rate(from_currency: str, to_currency: str) -> float:
    """Получить расчет по целевой валюте"""
    from_currency = validate_currency_code(from_currency)
    to_currency = validate_currency_code(to_currency)

    if from_currency not in EXCHANGE_RATES:
        raise ValueError(f'Неизвестный код валюты: "{from_currency}"')

    if to_currency not in EXCHANGE_RATES:
        raise ValueError(f'Неизвестный код валюты: "{to_currency}"')

    return EXCHANGE_RATES[from_currency] / EXCHANGE_RATES[to_currency]


def validate_amount(amount: float) -> None:
    """Валидирует сумму"""
    Wallet.validate_number(amount)

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
