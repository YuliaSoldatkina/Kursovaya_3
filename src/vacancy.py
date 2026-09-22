from typing import Any

import psycopg2


class VacancyLoader:
    """Загружает работодателей и вакансии в PostgreSQL."""

    def __init__(self, db_config: dict[str, str | None]) -> None:
        """Сохраняет настройки подключения к базе данных."""
        self.db_config = db_config

    def save_company(self, company: dict[str, Any]) -> int:
        """Сохраняет компанию и возвращает её идентификатор."""
        with psycopg2.connect(**self.db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO companies (hh_id, name, url)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (hh_id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        url = EXCLUDED.url
                    RETURNING company_id;
                    """,
                    (
                        company["id"],
                        company["name"],
                        company.get("alternate_url"),
                    ),
                )
                return cursor.fetchone()[0]

    def save_vacancies(
        self,
        company_id: int,
        vacancies: list[dict[str, Any]],
    ) -> int:
        """Сохраняет вакансии компании и возвращает их количество."""
        saved_count = 0

        with psycopg2.connect(**self.db_config) as connection:
            with connection.cursor() as cursor:
                for vacancy in vacancies:
                    salary = vacancy.get("salary") or {}

                    cursor.execute(
                        """
                        INSERT INTO vacancies (
                            hh_id,
                            company_id,
                            name,
                            salary_from,
                            salary_to,
                            salary_currency,
                            url
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hh_id)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            salary_from = EXCLUDED.salary_from,
                            salary_to = EXCLUDED.salary_to,
                            salary_currency = EXCLUDED.salary_currency,
                            url = EXCLUDED.url;
                        """,
                        (
                            vacancy["id"],
                            company_id,
                            vacancy["name"],
                            salary.get("from"),
                            salary.get("to"),
                            salary.get("currency"),
                            vacancy["alternate_url"],
                        ),
                    )
                    saved_count += 1

        return saved_count
