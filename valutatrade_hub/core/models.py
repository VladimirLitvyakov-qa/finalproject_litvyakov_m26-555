import hashlib
from datetime import datetime


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
