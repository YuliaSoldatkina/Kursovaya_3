CREATE TABLE IF NOT EXISTS companies (
    company_id SERIAL PRIMARY KEY,
    hh_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    url TEXT
);

CREATE TABLE IF NOT EXISTS vacancies (
    vacancy_id SERIAL PRIMARY KEY,
    hh_id INTEGER UNIQUE NOT NULL,
    company_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    salary_from INTEGER,
    salary_to INTEGER,
    salary_currency VARCHAR(10),
    url TEXT NOT NULL,
    CONSTRAINT fk_vacancies_company
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
);
