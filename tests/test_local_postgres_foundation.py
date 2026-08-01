import os
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def read_text(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


class LocalPostgresFoundationTest(unittest.TestCase):
    def test_compose_defines_postgres_service_and_app_dependency(self):
        compose = read_text("docker-compose.yml")

        self.assertIn("postgres:", compose)
        self.assertIn("image: postgres:16-alpine", compose)
        self.assertIn("POSTGRES_DB: ${POSTGRES_DB:-radar_cnpj}", compose)
        self.assertIn("${POSTGRES_PORT:-5432}:5432", compose)
        self.assertIn("./infra/postgres/init:/docker-entrypoint-initdb.d:ro", compose)
        self.assertIn("pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}", compose)
        self.assertIn("RADAR_CNPJ_POSTGRES_DSN:", compose)
        self.assertIn("condition: service_healthy", compose)
        self.assertIn("postgres-data:", compose)

    def test_env_example_documents_sqlite_and_postgres_roles(self):
        env = read_text(".env.example")

        self.assertIn("RADAR_CNPJ_DB=data/radar_cnpj.sqlite", env)
        self.assertIn("POSTGRES_DB=radar_cnpj", env)
        self.assertIn("POSTGRES_USER=radar_cnpj", env)
        self.assertIn("POSTGRES_PASSWORD=radar_cnpj_local", env)
        self.assertIn("POSTGRES_PORT=5432", env)
        self.assertIn("RADAR_CNPJ_POSTGRES_DSN=postgresql://", env)

    def test_bootstrap_sql_enables_required_extensions_and_schema(self):
        sql = read_text("infra/postgres/init/001_bootstrap.sql")

        self.assertIn("CREATE EXTENSION IF NOT EXISTS unaccent;", sql)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS pg_trgm;", sql)
        self.assertIn("CREATE SCHEMA IF NOT EXISTS receita_staging;", sql)
        self.assertIn("schema_bootstrap_log", sql)
        self.assertIn("phase-41", sql)

    def test_scripts_expose_check_and_generated_staging_ddl_flow(self):
        check_script = read_text("scripts/check_postgres.ps1")
        write_script = read_text("scripts/write_postgres_staging_sql.ps1")

        self.assertIn("docker compose ps -q", check_script)
        self.assertIn("pg_isready", check_script)
        self.assertIn("pg_extension", check_script)
        self.assertIn("information_schema.schemata", check_script)
        self.assertIn("postgres_staging_schema", write_script)
        self.assertIn("data/postgres/receita_staging.sql", write_script)


if __name__ == "__main__":
    unittest.main()
