import hashlib
import secrets
from datetime import datetime

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
    load_json,
    portfolio_to_dict,
    save_json,
    user_to_dict,
)

USERS_PATH = "data/users.json"
PORTFOLIOS_PATH = "data/portfolios.json"


def register(username: str, password: str) -> User:
    """Регистрирует нового пользователя"""
    if not isinstance(password, str):
        raise TypeError(f"password must be str, but got {type(password).__name__}")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов.")

    users = load_json(USERS_PATH)
    portfolios = load_json(PORTFOLIOS_PATH)

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
