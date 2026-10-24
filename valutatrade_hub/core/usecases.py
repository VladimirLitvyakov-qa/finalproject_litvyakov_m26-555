import hashlib
import secrets
from datetime import datetime, timedelta

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
    get_rate,
    load_json,
    portfolio_from_dict,
    portfolio_to_dict,
    save_json,
    user_from_dict,
    user_to_dict,
    validate_currency_code,
)

USERS_PATH = "data/users.json"
PORTFOLIOS_PATH = "data/portfolios.json"
RATES_PATH = "data/rates.json"


def register(username: str, password: str) -> User:
    """Регистрирует нового пользователя"""
    if not isinstance(password, str):
        raise TypeError(f"password must be str, but got {type(password).__name__}")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов.")

    users = load_json(USERS_PATH, [])

    if not isinstance(users, list):
        raise ValueError("Файл пользователей должен содержать список.")

    portfolios = load_json(PORTFOLIOS_PATH, [])

    if not isinstance(portfolios, list):
        raise ValueError("Файл портфелей должен содержать список.")

    max_user_id = 0

    for user in users:
        if user["username"] == username:
            raise ValueError(f'Имя - "{username}" занято! Попробуйте другое.')

        max_user_id = max(max_user_id, user["user_id"])

    user_id = max_user_id + 1
    salt = secrets.token_hex(16)
    password_and_salt = password + salt
    password_bytes = password_and_salt.encode("utf-8")
    hashed_password = hashlib.sha256(password_bytes).hexdigest()
    registration_date = datetime.now()

    new_user = User(user_id, username, hashed_password, salt, registration_date)

    user = user_to_dict(new_user)
    users.append(user)
    save_json(USERS_PATH, users)

    new_portfolio = Portfolio(new_user, {})
    portfolio = portfolio_to_dict(new_portfolio)
    portfolios.append(portfolio)
    save_json(PORTFOLIOS_PATH, portfolios)

    return new_user


def login(username: str, password: str) -> User:
    """Авторизует пользователя в системе"""
    users = load_json(USERS_PATH, [])

    if not isinstance(users, list):
        raise ValueError("Файл пользователей должен содержать список.")

    for user in users:
        if user["username"] == username:
            user_obj = user_from_dict(user)
            break
    else:
        raise ValueError(
            f'Пользователь с именем: "{username}" не найден в системе. '
            f"Попробуйте снова."
        )

    if not user_obj.verify_password(password):
        raise ValueError("Неверный пароль")

    return user_obj


def get_cached_rate(from_currency: str, to_currency: str) -> dict:
    """
    Возвращает курс из кеша, обновляя отсутствующие или устаревшие записи

    :param from_currency: код исходной валюты
    :param to_currency: код целевой валюты
    :return: словарь с курсом и временем его обновления
    :raises TypeError: если код валюты не является строкой
    :raises ValueError: если код пустой, курс неизвестен или кеш некорректен
    """
    from_currency = validate_currency_code(from_currency)
    to_currency = validate_currency_code(to_currency)
    currency_pair = from_currency + "_" + to_currency

    rates = load_json(RATES_PATH, {})

    if not isinstance(rates, dict):
        raise ValueError("Файл курсов должен содержать словарь.")

    cache = rates.get(currency_pair)

    if cache is not None:
        if not isinstance(cache, dict):
            raise ValueError("Запись курса должна содержать словарь.")

        updated_at = datetime.fromisoformat(cache["updated_at"])
        age = datetime.now() - updated_at

        if age < timedelta(minutes=5):
            return cache

    rate = get_rate(from_currency, to_currency)
    rates[currency_pair] = {"rate": rate, "updated_at": datetime.now().isoformat()}
    save_json(RATES_PATH, rates)

    return rates[currency_pair]


def get_portfolio(user: User) -> Portfolio:
    """
    Загружает портфель пользователя

    :param user: владелец портфеля
    :return: объект Portfolio
    :raises ValueError: если JSON некорректен, данные не являются списком
        или портфель пользователя не найден
    """
    portfolios = load_json(PORTFOLIOS_PATH, [])

    if not isinstance(portfolios, list):
        raise ValueError("Файл портфелей должен содержать список.")

    for portfolio in portfolios:
        if portfolio["user_id"] == user.user_id:
            return portfolio_from_dict(portfolio, user)
    else:
        raise ValueError("Портфель пользователя не найден")
