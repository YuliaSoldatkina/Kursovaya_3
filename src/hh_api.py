from typing import Any

import requests


class HeadHunterAPI:
    """Класс для получения данных о компаниях и вакансиях с hh.ru."""

    BASE_URL = "https://api.hh.ru"

    def __init__(self, user_agent: str = "CourseProject/1.0") -> None:
        """Инициализирует клиент API."""
        self.headers = {
            "User-Agent": user_agent,
        }

    def get_employer(self, employer_id: int) -> dict[str, Any]:
        """Возвращает данные работодателя по его идентификатору."""
        response = requests.get(
            f"{self.BASE_URL}/employers/{employer_id}",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_vacancies(self, employer_id: int) -> list[dict[str, Any]]:
        """Возвращает все вакансии указанного работодателя."""
        vacancies: list[dict[str, Any]] = []
        page = 0

        while True:
            response = requests.get(
                f"{self.BASE_URL}/vacancies",
                params={
                    "employer_id": employer_id,
                    "page": page,
                    "per_page": 100,
                },
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            vacancies.extend(data.get("items", []))

            pages = data.get("pages", 0)
            if page >= pages - 1:
                break

            page += 1

        return vacancies
