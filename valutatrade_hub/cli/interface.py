import shlex
from datetime import datetime

from valutatrade_hub.core.currencies import CURRENCIES
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy,
    get_cached_rate,
    get_portfolio_summary,
    login,
    register,
    sell,
)


def main():
    current_user = None

    while True:
        user_input = input("Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Некорректное значение: незакрытая кавычка. Попробуйте снова.")
            continue

        if len(args) < 1:
            print("Неизвестная команда. Попробуйте снова.")
            continue

        match args[0]:
            case "register":
                if len(args) != 5 or args[1] != "--username" or args[3] != "--password":
                    print("Некорректный формат. Попробуйте снова.")
                    continue
                else:
                    username = args[2]
                    password = args[4]

                try:
                    user = register(username, password)
                except ValueError as e:
                    print(e)
                    continue

                print(
                    f"Пользователь '{user.username}' зарегистрирован "
                    f"(id={user.user_id}). "
                    f"Войдите: login --username {user.username} --password ****"
                )
            case "login":
                if len(args) != 5 or args[1] != "--username" or args[3] != "--password":
                    print("Некорректный формат. Попробуйте снова.")
                    continue
                else:
                    username = args[2]
                    password = args[4]

                try:
                    current_user = login(username, password)
                except ValueError as e:
                    print(e)
                    continue

                print(f"Вы вошли как '{current_user.username}'")
            case "show-portfolio":
                if len(args) not in (1, 3):
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                if len(args) == 3 and args[1] != "--base":
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                if current_user is None:
                    print("Сначала выполните login.")
                    continue

                if len(args) == 1:
                    base_currency = "USD"
                else:
                    base_currency = args[2].upper()

                try:
                    portfolio = get_portfolio_summary(current_user, base_currency)
                except ApiRequestError as e:
                    print(e)
                    print("Повторите попытку позже или проверьте подключение к сети.")
                    continue
                except CurrencyNotFoundError as e:
                    print(e)
                    print("Поддерживаемые валюты: " + ", ".join(CURRENCIES))
                    continue
                except ValueError as e:
                    print(e)
                    continue

                wallets = portfolio["wallets"]
                if not wallets:
                    print("В портфеле пока нет кошельков.")
                    continue

                username = current_user.username
                print(f"Портфель пользователя '{username}' (база: {base_currency}):")

                base_precision = 8 if base_currency in ("BTC", "ETH") else 2
                for wallet in wallets:
                    code = wallet["currency_code"]
                    balance = wallet["balance"]
                    value = wallet["value"]
                    balance_precision = 8 if code in ("BTC", "ETH") else 2

                    print(
                        f"- {code}: {balance:.{balance_precision}f} → "
                        f"{value:.{base_precision}f} {base_currency}"
                    )

                print("-" * 33)
                print(f"ИТОГО: {portfolio['total']:.{base_precision}f} {base_currency}")
            case "buy" | "sell":
                if len(args) != 5 or args[1] != "--currency" or args[3] != "--amount":
                    print("Некорректный формат. Попробуйте снова.")
                    continue
                else:
                    current_code = args[2].upper()
                    amount = args[4]

                if current_user is None:
                    print("Сначала выполните login.")
                    continue

                try:
                    amount = float(amount)
                except ValueError:
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                if args[0] == "buy":
                    try:
                        buy_info = buy(current_user, current_code, amount)
                    except InsufficientFundsError as e:
                        print(e)
                        continue
                    except ApiRequestError as e:
                        print(e)
                        print(
                            "Повторите попытку позже или проверьте подключение к сети."
                        )
                        continue
                    except CurrencyNotFoundError as e:
                        print(e)
                        print("Поддерживаемые валюты: " + ", ".join(CURRENCIES))
                        continue
                    except ValueError as e:
                        print(e)
                        continue

                    balance_before = buy_info["balance_before"]
                    balance_after = buy_info["balance_after"]
                    rate = buy_info["rate"]
                    price = buy_info["price"]

                    print(
                        f"Покупка выполнена: {amount} {current_code} "
                        f"по курсу {rate:.2f} USD/{current_code}"
                    )
                    print("Изменения в портфеле:")
                    print(
                        f"{current_code}: было {balance_before} → стало {balance_after}"
                    )
                    print(f"Оценочная стоимость покупки: {price:.2f} USD ")
                else:
                    try:
                        sell_info = sell(current_user, current_code, amount)
                    except InsufficientFundsError as e:
                        print(e)
                        continue
                    except ApiRequestError as e:
                        print(e)
                        print(
                            "Повторите попытку позже или проверьте подключение к сети."
                        )
                        continue
                    except CurrencyNotFoundError as e:
                        print(e)
                        print("Поддерживаемые валюты: " + ", ".join(CURRENCIES))
                        continue
                    except ValueError as e:
                        print(e)
                        continue

                    balance_before = sell_info["balance_before"]
                    balance_after = sell_info["balance_after"]
                    rate = sell_info["rate"]
                    revenue = sell_info["revenue"]

                    print(
                        f"Продажа выполнена: {amount} {current_code} "
                        f"по курсу {rate:.2f} USD/{current_code}"
                    )
                    print("Изменения в портфеле:")
                    print(
                        f"{current_code}: было {balance_before} → стало {balance_after}"
                    )
                    print(f"Оценочная выручка: {revenue:.2f} USD ")
            case "get-rate":
                if len(args) != 5 or args[1] != "--from" or args[3] != "--to":
                    print("Некорректный формат. Попробуйте снова.")
                    continue
                else:
                    from_currency = args[2].upper()
                    to_currency = args[4].upper()

                try:
                    rate = get_cached_rate(from_currency, to_currency)
                except ApiRequestError as e:
                    print(e)
                    print("Повторите попытку позже или проверьте подключение к сети.")
                    continue
                except CurrencyNotFoundError as e:
                    print(e)
                    print("Поддерживаемые валюты: " + ", ".join(CURRENCIES))
                    continue
                except ValueError as e:
                    print(e)
                    continue

                exchange_rate = float(rate["rate"])
                updated_at = datetime.fromisoformat(rate["updated_at"])
                updated_at_text = updated_at.strftime("%Y-%m-%d %H:%M:%S")

                direct_precision = 8 if to_currency in ("BTC", "ETH") else 2
                reverse_precision = 8 if from_currency in ("BTC", "ETH") else 2

                print(
                    f"Курс {from_currency}→{to_currency}: "
                    f"{exchange_rate:.{direct_precision}f} "
                    f"(обновлено: {updated_at_text})"
                )
                print(
                    f"Обратный курс {to_currency}→{from_currency}: "
                    f"{1 / exchange_rate:.{reverse_precision}f}"
                )
            case "exit":
                break
            case _:
                print("Неизвестная команда.")


if __name__ == "__main__":
    main()
