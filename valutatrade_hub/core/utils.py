import json
import os


def load_users(users_path: str) -> list[dict]:
    """
    Читает JSON файл и возвращает список словарей

    :param users_path: путь до JSON-файла users
    :return: список словарей с пользователями или пустой список если файла нет
    """
    try:
        with open(users_path, encoding="UTF-8") as file:
            users = json.load(file)
    except FileNotFoundError:
        users = []
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in file.")

    return users


def save_users(users_path: str, users: list[dict]) -> None:
    """
    Сохраняет список пользователей в JSON-файл

    :param users_path: путь до JSON-файла users
    :param users: список с пользователями
    :return: None
    """
    directory = os.path.dirname(users_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(users_path, "w", encoding="UTF-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)
