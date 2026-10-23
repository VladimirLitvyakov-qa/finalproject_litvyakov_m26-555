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
        if not isinstance(amount, int | float):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}"
            )

        if amount < 0:
            raise ValueError("Баланс не может быть отрицательным.")

        self._balance = amount

    def deposit(self, amount: float) -> None:
        """Пополнить баланс"""
        if not isinstance(amount, int | float):
            raise TypeError(
                f"amount must be int or float, but got {type(amount).__name__}"
            )

        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной.")

        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снять с баланса"""
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
