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


def print_companies_count(db_manager: DBManager) -> None:
    """Выводит компании и количество их вакансий."""
    rows = db_manager.get_companies_and_vacancies_count()

    print("\nКомпании и количество вакансий:")
    for company_name, vacancies_count in rows:
        print(
            f"{company_name}: "
            f"{vacancies_count} вакансий"
        )


def print_all_vacancies(db_manager: DBManager) -> None:
    """Выводит список всех вакансий."""
    rows = db_manager.get_all_vacancies()

    print("\nВсе вакансии:")
    for row in rows:
        (
            company_name,
            vacancy_name,
            salary_from,
            salary_to,
            currency,
            url,
        ) = row

        salary = format_salary(
            salary_from,
            salary_to,
            currency,
        )

        print(
            f"{company_name} — {vacancy_name}; "
            f"зарплата: {salary}; "
            f"ссылка: {url}"
        )


def format_salary(
    salary_from: int | None,
    salary_to: int | None,
    currency: str | None,
) -> str:
    """Формирует человекочитаемое представление зарплаты."""
    currency_text = currency or "валюта не указана"

    if salary_from is not None and salary_to is not None:
        return f"от {salary_from} до {salary_to} {currency_text}"

    if salary_from is not None:
        return f"от {salary_from} {currency_text}"

    if salary_to is not None:
        return f"до {salary_to} {currency_text}"

    return "зарплата не указана"


def print_average_salary(db_manager: DBManager) -> None:
    """Выводит среднюю зарплату по вакансиям."""
    average_salary = db_manager.get_avg_salary()

    if average_salary is None:
        print("\nСредняя зарплата не определена.")
        return

    print(f"\nСредняя зарплата: {average_salary:.2f}")


def print_higher_salary_vacancies(
    db_manager: DBManager,
) -> None:
    """Выводит вакансии с зарплатой выше средней."""
    rows = db_manager.get_vacancies_with_higher_salary()

    print("\nВакансии с зарплатой выше средней:")

    if not rows:
        print("Таких вакансий нет.")
        return

    for company_name, vacancy_name, salary, currency, url in rows:
        print(
            f"{company_name} — {vacancy_name}; "
            f"зарплата: {salary:.2f} {currency or ''}; "
            f"ссылка: {url}"
        )


def print_keyword_vacancies(
    db_manager: DBManager,
    keyword: str,
) -> None:
    """Выводит вакансии по ключевому слову."""
    rows = db_manager.get_vacancies_with_keyword(keyword)

    print(
        f"\nВакансии, содержащие слово "
        f"«{keyword}»:"
    )

    if not rows:
        print("Вакансии не найдены.")
        return

    for row in rows:
        (
            company_name,
            vacancy_name,
            salary_from,
            salary_to,
            currency,
            url,
        ) = row

        salary = format_salary(
            salary_from,
            salary_to,
            currency,
        )

        print(
            f"{company_name} — {vacancy_name}; "
            f"зарплата: {salary}; "
            f"ссылка: {url}"
        )


def show_menu() -> None:
    """Выводит пункты меню."""
    print(
        "\nВыберите действие:\n"
        "1 — компании и количество вакансий\n"
        "2 — все вакансии\n"
        "3 — средняя зарплата\n"
        "4 — вакансии выше средней зарплаты\n"
        "5 — поиск по ключевому слову\n"
        "0 — выход"
    )


def run_user_interface(db_manager: DBManager) -> None:
    """Запускает пользовательское меню."""
    while True:
        show_menu()
        choice = input("Введите номер действия: ").strip()

        if choice == "1":
            print_companies_count(db_manager)
        elif choice == "2":
            print_all_vacancies(db_manager)
        elif choice == "3":
            print_average_salary(db_manager)
        elif choice == "4":
            print_higher_salary_vacancies(db_manager)
        elif choice == "5":
            keyword = input(
                "Введите ключевое слово, например python: "
            ).strip()

            if keyword:
                print_keyword_vacancies(
                    db_manager,
                    keyword,
                )
            else:
                print("Ключевое слово не должно быть пустым.")
        elif choice == "0":
            print("Работа программы завершена.")
            break
        else:
            print("Некорректный выбор. Введите число от 0 до 5.")


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
    run_user_interface(db_manager)