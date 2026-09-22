from src.db_manager import DBManager
from pathlib import Path
from typing import Any

from src.config import DB_CONFIG, EMPLOYERS
from src.database import DatabaseCreator
from src.file_manager import VacancyFileManager
from src.vacancy import VacancyLoader


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = PROJECT_ROOT / "sql" / "create_tables.sql"
DATA_PATH = PROJECT_ROOT / "data" / "hh_vacancies.json"


def make_company_url(company_id: int) -> str:
    """Формирует ссылку на страницу работодателя."""
    return f"https://hh.ru/employer/{company_id}"


def prepare_companies(
    vacancies: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Собирает уникальных работодателей из вакансий."""
    companies: dict[int, dict[str, Any]] = {}

    for vacancy in vacancies:
        employer = vacancy.get("employer") or {}
        employer_id = employer.get("id")

        if employer_id is None:
            continue

        companies[int(employer_id)] = {
            "id": int(employer_id),
            "name": employer.get("name", "Неизвестная компания"),
            "alternate_url": employer.get(
                "alternate_url",
                make_company_url(int(employer_id)),
            ),
        }

    return companies


def main() -> None:
    """Создаёт базу, таблицы и загружает данные из резервного файла."""
    database_creator = DatabaseCreator(DB_CONFIG)
    database_creator.create_database()
    database_creator.create_tables(SQL_PATH)

    file_manager = VacancyFileManager(DATA_PATH)
    vacancies = file_manager.read_data()
    companies = prepare_companies(vacancies)

    loader = VacancyLoader(DB_CONFIG)

    total_vacancies = 0

    for company in companies.values():
        company_id = loader.save_company(company)

        company_vacancies = [
            vacancy
            for vacancy in vacancies
            if int((vacancy.get("employer") or {}).get("id", 0))
            == company["id"]
        ]

        total_vacancies += loader.save_vacancies(
            company_id,
            company_vacancies,
        )

        print(
            f"{company['name']}: "
            f"загружено вакансий — {len(company_vacancies)}"
        )

    print(
        f"\nИз файла загружено компаний: {len(companies)}"
    )
    print(f"Из файла загружено вакансий: {total_vacancies}")

    loaded_ids = set(companies)
    additional_companies = [
        {
            "id": employer_id,
            "name": employer_name,
            "alternate_url": make_company_url(employer_id),
        }
        for employer_name, employer_id in EMPLOYERS.items()
        if employer_id not in loaded_ids
    ][:5]

    for company in additional_companies:
        loader.save_company(company)

    print(
        f"Всего компаний в базе после загрузки: "
        f"{len(companies) + len(additional_companies)}"
    )


if __name__ == "__main__":
    main()


    db_manager = DBManager(DB_CONFIG)

    print("\nКомпании и количество вакансий:")
    for row in db_manager.get_companies_and_vacancies_count():
        print(f"- {row[0]}: {row[1]} вакансий")

    average_salary = db_manager.get_avg_salary()
    print(f"\nСредняя зарплата: {average_salary}")

    print("\nВакансии выше средней зарплаты:")
    for row in db_manager.get_vacancies_with_higher_salary():
        print(f"- {row[0]} — {row[1]}: {row[2]} {row[3]}")

    print("\nВакансии по ключевому слову «python»:")
    for row in db_manager.get_vacancies_with_keyword("python"):
        print(f"- {row[0]} — {row[1]}")

    print("\nВсего вакансий:", len(db_manager.get_all_vacancies()))
