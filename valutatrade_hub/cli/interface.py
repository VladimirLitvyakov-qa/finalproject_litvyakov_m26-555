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
    get_rates,
    login,
    register,
    sell,
)
from valutatrade_hub.core.utils import validate_amount
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def main():
    current_user = None

    settings = SettingsLoader()
    setup_logging()
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
                    base_currency = settings.get("default_base_currency")
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

                base_precision = 8 if base_currency in ("BTC", "ETH", "SOL") else 2
                for wallet in wallets:
                    code = wallet["currency_code"]
                    balance = wallet["balance"]
                    value = wallet["value"]
                    balance_precision = 8 if code in ("BTC", "ETH", "SOL") else 2

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

                direct_precision = 8 if to_currency in ("BTC", "ETH", "SOL") else 2
                reverse_precision = 8 if from_currency in ("BTC", "ETH", "SOL") else 2

                print(
                    f"Курс {from_currency}→{to_currency}: "
                    f"{exchange_rate:.{direct_precision}f} "
                    f"(обновлено: {updated_at_text})"
                )
                print(
                    f"Обратный курс {to_currency}→{from_currency}: "
                    f"{1 / exchange_rate:.{reverse_precision}f}"
                )
            case "update-rates":
                if len(args) not in (1, 3):
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                if len(args) == 3 and args[1] != "--source":
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                source = args[2].lower() if len(args) == 3 else None

                if source not in (None, "coingecko", "exchangerate"):
                    print("Допустимые источники: coingecko, exchangerate.")
                    continue

                if source == "coingecko":
                    clients = [CoinGeckoClient()]
                elif source == "exchangerate":
                    clients = [ExchangeRateApiClient()]
                else:
                    clients = [CoinGeckoClient(), ExchangeRateApiClient()]

                storage = RatesStorage()
                updater = RatesUpdater(clients, storage)

                try:
                    result = updater.run_update()
                except ApiRequestError as error:
                    print(error)
                    continue

                updated_at = datetime.fromisoformat(result["last_refresh"])
                updated_at_text = updated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

                print(
                    f"Обновлено курсов: {result['updated_count']}. "
                    f"Последнее обновление: {updated_at_text}"
                )

                if result["failed_sources"]:
                    print("Обновление завершено с ошибками.")
                    print(
                        "Не ответили источники: " + ", ".join(result["failed_sources"])
                    )
                    print(f"Подробности: {settings.get('log_path')}")
                else:
                    print("Обновление успешно завершено.")
            case "show-rates":
                currency = None
                top = None
                base_currency = "USD"
                used_flags = set()
                valid_args = True

                if len(args) % 2 == 0:
                    print("Некорректный формат. Попробуйте снова.")
                    continue

                for index in range(1, len(args), 2):
                    flag = args[index]
                    value = args[index + 1]

                    if flag in used_flags:
                        print(f"Аргумент {flag} указан повторно.")
                        valid_args = False
                        break

                    used_flags.add(flag)

                    if flag == "--currency":
                        currency = value.upper()

                    elif flag == "--base":
                        base_currency = value.upper()

                    elif flag == "--top":
                        try:
                            top = int(value)
                        except ValueError:
                            print("--top должен быть положительным целым числом.")
                            valid_args = False
                            break

                        if top <= 0:
                            print("--top должен быть положительным целым числом.")
                            valid_args = False
                            break

                    else:
                        print(f"Неизвестный аргумент: {flag}")
                        valid_args = False
                        break

                if not valid_args:
                    continue

                try:
                    cache = get_rates()
                except ValueError as error:
                    print(error)
                    continue

                pairs = cache["pairs"]

                try:
                    if base_currency == "USD":
                        base_rate = 1.0
                    else:
                        base_record = pairs.get(base_currency + "_USD")

                        if base_record is None:
                            raise ValueError(
                                f"Курс для '{base_currency}' не найден в кеше."
                            )

                        base_rate = base_record["rate"]
                        validate_amount(base_rate)

                    rows = []

                    for currency_pair, values in pairs.items():
                        code, quote = currency_pair.split("_", 1)

                        if quote != "USD":
                            raise ValueError(
                                f"Ожидалась пара к USD, получена '{currency_pair}'."
                            )

                        if currency is not None and code != currency:
                            continue

                        rate = values["rate"]
                        validate_amount(rate)

                        rows.append(
                            {
                                "code": code,
                                "pair": code + "_" + base_currency,
                                "rate": rate / base_rate,
                            }
                        )

                except (ValueError, TypeError, KeyError) as error:
                    print(f"Не удалось прочитать курсы: {error}")
                    continue

                if currency is not None and not rows:
                    print(f"Курс для '{currency}' не найден в кеше.")
                    continue

                if top is not None:
                    rows = [
                        row
                        for row in rows
                        if row["code"] in ParserConfig.CRYPTO_CURRENCIES
                    ]
                    rows.sort(key=lambda row: row["rate"], reverse=True)
                    rows = rows[:top]
                else:
                    rows.sort(key=lambda row: row["pair"])

                if not rows:
                    print("Нет курсов, соответствующих указанным фильтрам.")
                    continue

                print(f"Rates from cache (updated at {cache['last_refresh']}):")

                for row in rows:
                    rate_text = f"{row['rate']:.8f}".rstrip("0").rstrip(".")

                    if "." not in rate_text:
                        rate_text += ".00"

                    print(f"- {row['pair']}: {rate_text}")
            case "exit":
                break
            case _:
                print("Неизвестная команда.")


if __name__ == "__main__":
    main()
