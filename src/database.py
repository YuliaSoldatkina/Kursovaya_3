from pathlib import Path

import psycopg2
from psycopg2 import sql


class DatabaseCreator:
    """Создаёт базу данных и таблицы проекта."""

    def __init__(
        self,
        db_config: dict[str, str | None],
    ) -> None:
        """Инициализирует настройки подключения."""
        self.db_config = db_config

    def create_database(self) -> None:
        """Создаёт базу данных проекта, если её ещё нет."""
        database_name = self.db_config["dbname"]

        connection_config = self.db_config.copy()
        connection_config["dbname"] = "postgres"

        connection = psycopg2.connect(**connection_config)
        connection.autocommit = True

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (database_name,),
                )

                if cursor.fetchone() is None:
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {}").format(
                            sql.Identifier(database_name)
                        )
                    )
        finally:
            connection.close()

    def create_tables(self, sql_path: Path) -> None:
        """Создаёт таблицы в базе данных проекта."""
        query = sql_path.read_text(encoding="utf-8")

        connection = psycopg2.connect(**self.db_config)

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
        finally:
            connection.close()
