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
    validate_amount,
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


def save_portfolio(portfolio: Portfolio) -> None:
    """
    Сохраняет портфель пользователя

    :param portfolio: объект Portfolio
    :raises ValueError: данные не являются списком или
        портфель пользователя не найден
    """
    portfolios = load_json(PORTFOLIOS_PATH, [])

    if not isinstance(portfolios, list):
        raise ValueError("Файл портфелей должен содержать список.")

    for i, data in enumerate(portfolios):
        if data["user_id"] == portfolio.user_id:
            portfolios[i] = portfolio_to_dict(portfolio)
            save_json(PORTFOLIOS_PATH, portfolios)
            break
    else:
        raise ValueError("Портфель пользователя не найден")


def buy(user: User, currency_code: str, amount: float) -> None:
    """
    Покупает валюту за средства USD-кошелька

    :param user: пользователь, совершающий покупку
    :param currency_code: код покупаемой валюты
    :param amount: количество покупаемой валюты
    :raises TypeError: если пользователь, код валюты или сумма имеют неверный тип
    :raises ValueError: если сумма неположительная, валюта недопустима,
        недостаточно USD или данные хранилища некорректны
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    currency_code = validate_currency_code(currency_code)
    validate_amount(amount)

    if currency_code == "USD":
        raise ValueError("Нельзя купить USD за USD.")

    portfolio = get_portfolio(user)
    wallets = portfolio.wallets

    cached_data = get_cached_rate(currency_code, "USD")
    price = amount * cached_data["rate"]

    if "USD" not in wallets:
        raise ValueError("Недостаточно средств в USD.")

    usd_wallet = wallets["USD"]

    if usd_wallet.balance < price:
        raise ValueError("Недостаточно средств в USD.")

    if currency_code not in wallets:
        portfolio.add_currency(currency_code)

    target_wallet = portfolio.get_wallet(currency_code)
    usd_wallet.withdraw(price)
    target_wallet.deposit(amount)

    save_portfolio(portfolio)


def sell(user: User, currency_code: str, amount: float) -> None:
    """
    Продаёт валюту с зачислением выручки в USD-кошелёк

    :param user: пользователь, совершающий продажу
    :param currency_code: код продаваемой валюты
    :param amount: количество продаваемой валюты
    :raises TypeError: если пользователь, код валюты или сумма имеют неверный тип
    :raises ValueError: если сумма неположительная, валюта недопустима,
        кошелёк отсутствует, средств недостаточно или данные хранилища некорректны
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    currency_code = validate_currency_code(currency_code)
    validate_amount(amount)

    if currency_code == "USD":
        raise ValueError("Нельзя продать USD за USD.")

    portfolio = get_portfolio(user)
    wallets = portfolio.wallets

    if currency_code not in wallets:
        raise ValueError(f'Кошелёк "{currency_code}" не существует')

    sell_wallet = wallets[currency_code]
    if sell_wallet.balance < amount:
        raise ValueError(f'Недостаточно средств в "{currency_code}"')

    cached_data = get_cached_rate(currency_code, "USD")
    revenue = amount * cached_data["rate"]

    if "USD" not in wallets:
        portfolio.add_currency("USD")

    usd_wallet = portfolio.get_wallet("USD")
    sell_wallet.withdraw(amount)
    usd_wallet.deposit(revenue)

    save_portfolio(portfolio)
