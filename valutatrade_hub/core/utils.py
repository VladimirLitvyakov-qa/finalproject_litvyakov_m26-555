import json
import os
from datetime import datetime

from valutatrade_hub.core.models import User


def load_json(path: str) -> list[dict]:
    """
    Читает JSON файл и возвращает список словарей

    :param path: путь до JSON-файла
    :return: список словарей
    """
    try:
        with open(path, encoding="UTF-8") as file:
            result = json.load(file)
    except FileNotFoundError:
        result = []
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in file.")

    return result


def save_json(path: str, data: list[dict]) -> None:
    """
    Сохраняет список data в JSON-файл

    :param path: путь до JSON-файл
    :param data: список словарей для сохранения
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="UTF-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def user_from_dict(data: dict) -> User:
    """
    Создает пользователя из словаря

    :param data: словарь
    :return: объект User
    """
    if not isinstance(data, dict):
        raise TypeError(f"data must be dict, but got {type(data).__name__}")

    user_id = data["user_id"]
    username = data["username"]
    hashed_password = data["hashed_password"]
    salt = data["salt"]
    registration_date = datetime.fromisoformat(data["registration_date"])

    return User(user_id, username, hashed_password, salt, registration_date)


def user_to_dict(user: User) -> dict:
    """
    Преобразовывает из объекта пользователя в словарь

    :param user: объект User
    :return: словарь с данными пользователя
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be User, but got {type(user).__name__}")

    user_id = user.user_id
    username = user.username
    hashed_password = user.hashed_password
    salt = user.salt
    registration_date = user.registration_date.isoformat()

    return {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": registration_date,
    }
