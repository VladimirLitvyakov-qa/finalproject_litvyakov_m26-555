import hashlib
from datetime import datetime

EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.1,
    "RUB": 0.01,
    "BTC": 60000.0,
    "ETH": 3000.0,
}


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        self.currency_code = currency_code
        self.balance = balance

    @property
    def balance(self) -> float:
        """Получить баланс"""
        return self._balance

    @balance.setter
    def balance(self, amount: float) -> None:
        """Установить баланс"""
        if isinstance(amount, bool):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}."
            )

        if not isinstance(amount, int | float):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}"
            )

        if amount < 0:
            raise ValueError("Баланс не может быть отрицательным.")

        self._balance = amount

    def deposit(self, amount: float) -> None:
        """Пополнить баланс"""
        if isinstance(amount, bool):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}."
            )

        if not isinstance(amount, int | float):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}"
            )

        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной.")

        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снять с баланса"""
        if isinstance(amount, bool):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}."
            )

        if not isinstance(amount, int | float):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}"
            )

        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной.")

        if amount > self.balance:
            raise ValueError("Недостаточно средств на балансе")

        self.balance -= amount

    def get_balance_info(self) -> str:
        """Получить информацию о балансе"""
        return f"На балансе: {self.balance:.2f} {self.currency_code}"


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        self.username = username
        self._user_id = user_id
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def username(self) -> str:
        """Получить имя пользователя"""
        return self._username

    @username.setter
    def username(self, new_name: str) -> None:
        """Изменить имя пользователя"""
        if not isinstance(new_name, str):
            raise TypeError(f"new_name must be str, but got {type(new_name).__name__}")

        if not new_name:
            raise ValueError("Имя не может быть пустым.")

        self._username = new_name

    @property
    def user_id(self) -> int:
        """Получить id пользователя"""
        return self._user_id

    @property
    def hashed_password(self) -> str:
        """Получить хэшированный пароль"""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Получить соль"""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Получить дату регистрации"""
        return self._registration_date

    def get_user_info(self) -> dict:
        """Получить информацию о пользователе"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date,
        }

    def change_password(self, new_password: str) -> None:
        """Изменить пароль"""
        if not isinstance(new_password, str):
            raise TypeError(
                f"new_password must be str, but got {type(new_password).__name__}"
            )

        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")

        new_password_and_salt = new_password + self.salt
        password_bytes = new_password_and_salt.encode("utf-8")
        new_hashed_password = hashlib.sha256(password_bytes).hexdigest()

        self._hashed_password = new_hashed_password

    def verify_password(self, password: str) -> bool:
        """Проверить пароль"""
        if not isinstance(password, str):
            raise TypeError(f"password must be str, but got {type(password).__name__}")

        password_and_salt = password + self.salt
        password_bytes = password_and_salt.encode("utf-8")
        password_hash = hashlib.sha256(password_bytes).hexdigest()

        return password_hash == self.hashed_password


class Portfolio:
    def __init__(self, user: User, wallets: dict[str, Wallet]) -> None:
        self._user = user
        self._wallets = wallets

    @property
    def user_id(self) -> int:
        """Получить user_id."""
        return self._user.user_id

    @property
    def user(self) -> User:
        """Получить владельца портфеля."""
        return self._user

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Получить портфель кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> None:
        """Добавляет новый кошелек в портфель."""
        if not isinstance(currency_code, str):
            raise TypeError(
                f"currency_code must be str, but got {type(currency_code).__name__}"
            )

        if not currency_code:
            raise ValueError("Код валюты не может быть пустым.")

        currency_code = currency_code.upper()

        if currency_code in self.wallets:
            raise ValueError("Данная валюта уже есть в кошельке")

        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Wallet:
        """Получить кошелек по коду валюты."""
        if not isinstance(currency_code, str):
            raise TypeError(
                f"currency_code must be str, but got {type(currency_code).__name__}"
            )

        if not currency_code:
            raise ValueError("Код валюты не может быть пустым.")

        currency_code = currency_code.upper()

        return self.wallets[currency_code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Получить сумму всего баланса в указанной валюте"""
        if not isinstance(base_currency, str):
            raise TypeError(
                f"base_currency must be str, but got {type(base_currency).__name__}"
            )

        if not base_currency:
            raise ValueError("Код валюты не может быть пустым.")

        base_currency = base_currency.upper()

        if base_currency not in EXCHANGE_RATES:
            raise ValueError("Неизвестная валюта.")

        wallet_values_usd = []
        for code, wallet in self._wallets.items():
            value = wallet.balance * EXCHANGE_RATES[code]
            wallet_values_usd.append(value)

        return sum(wallet_values_usd) / EXCHANGE_RATES[base_currency]
