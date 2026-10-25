import logging
from functools import wraps
from inspect import signature


def log_action(verbose: bool = False):
    """
    Логирует успешные и неуспешные торговые операции

    :param verbose: добавлять баланс до и после операции
    """

    def decorator(func):
        function_signature = signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("valutatrade_hub")
            action = func.__name__.upper()
            context = action

            try:
                arguments = function_signature.bind(*args, **kwargs).arguments

                user = arguments.get("user")
                username = getattr(user, "username", None)
                currency_code = arguments.get("currency_code")
                amount = arguments.get("amount")

                context = (
                    f"{action} user={username!r} "
                    f"currency={currency_code!r} amount={amount!r} "
                    f"base='USD'"
                )

                result = func(*args, **kwargs)

            except Exception as error:
                logger.info(
                    f"{context} result=ERROR "
                    f"error_type={type(error).__name__} "
                    f"error_message={str(error)!r}"
                )
                raise

            message = (
                f"{action} user={username!r} "
                f"currency={result['currency_code']!r} "
                f"amount={result['amount']} "
                f"rate={result['rate']} base='USD' result=OK"
            )

            if verbose:
                message += (
                    f" balance_before={result['balance_before']}"
                    f" balance_after={result['balance_after']}"
                )

            logger.info(message)
            return result

        return wrapper

    return decorator
