import json
from pathlib import Path
from typing import Any


class VacancyFileManager:
    """Читает данные о вакансиях из JSON-файла."""

    def __init__(self, file_path: Path) -> None:
        """Сохраняет путь к JSON-файлу."""
        self.file_path = file_path

    def read_data(self) -> list[dict[str, Any]]:
        """Возвращает список записей из JSON-файла."""
        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ("items", "vacancies", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return value

        raise ValueError(
            "JSON-файл должен содержать список вакансий "
            "или словарь с ключом items, vacancies либо data."
        )
