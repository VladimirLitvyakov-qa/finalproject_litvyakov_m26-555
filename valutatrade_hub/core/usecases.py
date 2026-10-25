import hashlib
import secrets
from datetime import datetime, timedelta

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError, InsufficientFundsError
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
    get_rate,
    portfolio_from_dict,
    portfolio_to_dict,
    user_from_dict,
    user_to_dict,
    validate_amount,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

db = DatabaseManager()
settings = SettingsLoader()


def register(username: str, password: str) -> User:
    """Регистрирует нового пользователя"""
    if not isinstance(password, str):
        raise TypeError(f"password must be str, but got {type(password).__name__}")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов.")

    users = db.load_users()
    portfolios = db.load_portfolios()

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
    db.save_users(users)

    new_portfolio = Portfolio(new_user, {})
    portfolio = portfolio_to_dict(new_portfolio)
    portfolios.append(portfolio)
    db.save_portfolios(portfolios)

    return new_user


def login(username: str, password: str) -> User:
    """Авторизует пользователя в системе"""
    users = db.load_users()

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
    :raises ValueError: если код пустой или данные кеша некорректны
    :raises CurrencyNotFoundError: если код валюты неизвестен
    :raises ApiRequestError: если произошёл сбой при обращении к источнику курсов
    """
    from_currency = get_currency(from_currency).code
    to_currency = get_currency(to_currency).code
    currency_pair = from_currency + "_" + to_currency

    rates = db.load_rates()
    cache = rates.get(currency_pair)

    if cache is not None:
        if not isinstance(cache, dict):
            raise ValueError("Запись курса должна содержать словарь.")

        updated_at = datetime.fromisoformat(cache["updated_at"])
        age = datetime.now() - updated_at

        if age < timedelta(seconds=settings.get("rates_ttl_seconds")):
            validate_amount(cache["rate"])
            return cache

    try:
        rate = get_rate(from_currency, to_currency)
    except (ConnectionError, TimeoutError) as error:
        raise ApiRequestError(str(error)) from error

    rates[currency_pair] = {"rate": rate, "updated_at": datetime.now().isoformat()}
    db.save_rates(rates)

    return rates[currency_pair]


def get_portfolio(user: User) -> Portfolio:
    """
    Загружает портфель пользователя

    :param user: владелец портфеля
    :return: объект Portfolio
    :raises ValueError: если JSON некорректен, данные не являются списком
        или портфель пользователя не найден
    """
    portfolios = db.load_portfolios()

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
    portfolios = db.load_portfolios()

    for i, data in enumerate(portfolios):
        if data["user_id"] == portfolio.user_id:
            portfolios[i] = portfolio_to_dict(portfolio)
            db.save_portfolios(portfolios)
            break
    else:
        raise ValueError("Портфель пользователя не найден")


def get_portfolio_summary(user: User, base_currency: str = "USD") -> dict:
    """
    Подготавливает сводку портфеля пользователя в базовой валюте

    :param user: владелец портфеля
    :param base_currency: базовая валюта для расчёта стоимости
    :return: словарь с данными кошельков, общей стоимостью и базовой валютой
    :raises TypeError: если пользователь или код валюты имеют неверный тип
    :raises ValueError: если код пустой, портфель не найден
        или данные хранилища некорректны
    :raises CurrencyNotFoundError: если код валюты неизвестен
    :raises ApiRequestError: если произошёл сбой при обращении к источнику курсов
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    base_currency = get_currency(base_currency).code
    portfolio = get_portfolio(user)

    wallet_details = []
    total = 0.0

    for code, wallet in portfolio.wallets.items():
        rate = get_cached_rate(code, base_currency)["rate"]
        value = rate * wallet.balance
        result = {"currency_code": code, "balance": wallet.balance, "value": value}
        wallet_details.append(result)
        total += value

    result = {"wallets": wallet_details, "total": total, "base_currency": base_currency}
    return result


@log_action(verbose=True)
def buy(user: User, currency_code: str, amount: float) -> dict:
    """
    Покупает валюту за средства USD-кошелька

    :param user: пользователь, совершающий покупку
    :param currency_code: код покупаемой валюты
    :param amount: количество покупаемой валюты
    :return: словарь с кодом и количеством валюты, балансами до и после покупки,
        использованным курсом и стоимостью покупки в USD
    :raises TypeError: если пользователь, код валюты или сумма имеют неверный тип
    :raises ValueError: если сумма недопустима, запрошена покупка USD за USD,
        данные хранилища некорректны
    :raises InsufficientFundsError: если недостаточно средств в USD
    :raises CurrencyNotFoundError: если код валюты неизвестен
    :raises ApiRequestError: если произошёл сбой при обращении к источнику курсов
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    currency_code = get_currency(currency_code).code
    validate_amount(amount)

    if currency_code == "USD":
        raise ValueError("Нельзя купить USD за USD.")

    portfolio = get_portfolio(user)
    wallets = portfolio.wallets
    cached_data = get_cached_rate(currency_code, "USD")
    price = amount * cached_data["rate"]

    if "USD" not in wallets:
        raise InsufficientFundsError(0, price, "USD")

    usd_wallet = wallets["USD"]

    if usd_wallet.balance < price:
        raise InsufficientFundsError(usd_wallet.balance, price, "USD")

    if currency_code not in wallets:
        portfolio.add_currency(currency_code)

    target_wallet = portfolio.get_wallet(currency_code)
    usd_wallet.withdraw(price)
    balance_before = target_wallet.balance
    target_wallet.deposit(amount)
    balance_after = target_wallet.balance

    save_portfolio(portfolio)

    result = {
        "currency_code": currency_code,
        "amount": amount,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "rate": cached_data["rate"],
        "price": price,
    }

    return result


@log_action(verbose=True)
def sell(user: User, currency_code: str, amount: float) -> dict:
    """
    Продаёт валюту с зачислением выручки в USD-кошелёк

    :param user: пользователь, совершающий продажу
    :param currency_code: код продаваемой валюты
    :param amount: количество продаваемой валюты
    :return: словарь с кодом и количеством валюты, балансами до и после продажи,
        использованным курсом и оценочной выручкой в USD
    :raises TypeError: если пользователь, код валюты или сумма имеют неверный тип
    :raises ValueError: если сумма недопустима, запрошена продажа USD за USD,
        кошелёк отсутствует или данные хранилища некорректны
    :raises InsufficientFundsError: если недостаточно продаваемой валюты
    :raises CurrencyNotFoundError: если код валюты неизвестен
    :raises ApiRequestError: если произошёл сбой при обращении к источнику курсов
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    currency_code = get_currency(currency_code).code
    validate_amount(amount)

    if currency_code == "USD":
        raise ValueError("Нельзя продать USD за USD.")

    portfolio = get_portfolio(user)
    wallets = portfolio.wallets

    if currency_code not in wallets:
        raise ValueError(
            f"У вас нет кошелька '{currency_code}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    sell_wallet = wallets[currency_code]
    balance = sell_wallet.balance
    if balance < amount:
        raise InsufficientFundsError(balance, amount, currency_code)

    cached_data = get_cached_rate(currency_code, "USD")
    revenue = amount * cached_data["rate"]

    if "USD" not in wallets:
        portfolio.add_currency("USD")

    usd_wallet = portfolio.get_wallet("USD")
    sell_wallet.withdraw(amount)
    balance_after = sell_wallet.balance
    usd_wallet.deposit(revenue)

    save_portfolio(portfolio)

    result = {
        "currency_code": currency_code,
        "amount": amount,
        "balance_before": balance,
        "balance_after": balance_after,
        "rate": cached_data["rate"],
        "revenue": revenue,
    }

    return result
