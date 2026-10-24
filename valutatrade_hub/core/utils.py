import json
import os


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
