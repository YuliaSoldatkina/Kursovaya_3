from typing import Any

import psycopg2


class DBManager:
    """Класс для выполнения запросов к базе данных проекта."""

    def __init__(self, db_config: dict[str, str | None]) -> None:
        """Сохраняет настройки подключения к базе данных."""
        self.db_config = db_config

    def get_companies_and_vacancies_count(self) -> list[tuple[Any, ...]]:
        """Возвращает компании и количество вакансий у каждой компании."""
        query = """
            SELECT
                c.name,
                COUNT(v.vacancy_id) AS vacancies_count
            FROM companies AS c
            LEFT JOIN vacancies AS v
                ON c.company_id = v.company_id
            GROUP BY c.company_id, c.name
            ORDER BY vacancies_count DESC, c.name;
        """
        return self._fetch_all(query)

    def get_all_vacancies(self) -> list[tuple[Any, ...]]:
        """Возвращает все вакансии с названием компании и зарплатой."""
        query = """
            SELECT
                c.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.salary_currency,
                v.url
            FROM vacancies AS v
            JOIN companies AS c
                ON v.company_id = c.company_id
            ORDER BY c.name, v.name;
        """
        return self._fetch_all(query)

    def get_avg_salary(self) -> float | None:
        """Возвращает среднюю зарплату по вакансиям."""
        query = """
            SELECT AVG(
                CASE
                    WHEN salary_from IS NOT NULL
                         AND salary_to IS NOT NULL
                        THEN (salary_from + salary_to) / 2.0
                    WHEN salary_from IS NOT NULL
                        THEN salary_from
                    WHEN salary_to IS NOT NULL
                        THEN salary_to
                    ELSE NULL
                END
            )
            FROM vacancies;
        """
        result = self._fetch_one(query)
        return result[0] if result else None

    def get_vacancies_with_higher_salary(self) -> list[tuple[Any, ...]]:
        """Возвращает вакансии с зарплатой выше средней."""
        query = """
            WITH vacancy_salary AS (
                SELECT
                    v.*,
                    CASE
                        WHEN v.salary_from IS NOT NULL
                             AND v.salary_to IS NOT NULL
                            THEN (v.salary_from + v.salary_to) / 2.0
                        WHEN v.salary_from IS NOT NULL
                            THEN v.salary_from
                        WHEN v.salary_to IS NOT NULL
                            THEN v.salary_to
                        ELSE NULL
                    END AS average_salary
                FROM vacancies AS v
            )
            SELECT
                c.name AS company_name,
                vacancy_salary.name AS vacancy_name,
                vacancy_salary.average_salary,
                vacancy_salary.salary_currency,
                vacancy_salary.url
            FROM vacancy_salary
            JOIN companies AS c
                ON vacancy_salary.company_id = c.company_id
            WHERE vacancy_salary.average_salary > (
                SELECT AVG(average_salary)
                FROM vacancy_salary
            )
            ORDER BY vacancy_salary.average_salary DESC;
        """
        return self._fetch_all(query)

    def get_vacancies_with_keyword(
        self,
        keyword: str,
    ) -> list[tuple[Any, ...]]:
        """Возвращает вакансии, содержащие ключевое слово в названии."""
        query = """
            SELECT
                c.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.salary_currency,
                v.url
            FROM vacancies AS v
            JOIN companies AS c
                ON v.company_id = c.company_id
            WHERE v.name ILIKE %s
            ORDER BY v.name;
        """
        return self._fetch_all(query, (f"%{keyword}%",))

    def _fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> list[tuple[Any, ...]]:
        """Выполняет запрос и возвращает все строки."""
        with psycopg2.connect(**self.db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def _fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> tuple[Any, ...] | None:
        """Выполняет запрос и возвращает одну строку."""
        with psycopg2.connect(**self.db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
