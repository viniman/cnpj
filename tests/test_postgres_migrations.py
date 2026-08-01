import os
import re
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MIGRATIONS_DIR = os.path.join(ROOT, "infra", "postgres", "migrations")


def read_text(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


class PostgresMigrationsTest(unittest.TestCase):
    def test_staging_migrations_use_timestamp_slug_pattern(self):
        filenames = sorted(name for name in os.listdir(MIGRATIONS_DIR) if name.endswith(".sql"))

        self.assertIn("20260801190000_create_receita_staging_raw_tables.sql", filenames)
        for filename in filenames:
            self.assertRegex(filename, r"^\d{14}_[a-z0-9_]+\.sql$")

    def test_first_staging_migration_creates_raw_tables_and_indexes(self):
        sql = read_text("infra/postgres/migrations/20260801190000_create_receita_staging_raw_tables.sql")

        self.assertIn("CREATE TABLE IF NOT EXISTS receita_staging.empresas_raw", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS receita_staging.estabelecimentos_raw", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS receita_staging.socios_raw", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS receita_staging.simples_raw", sql)
        self.assertIn("idx_receita_estab_cnpj_completo", sql)
        self.assertIn("gin_trgm_ops", sql)
        self.assertNotIn("schema_bootstrap_log", sql)

    def test_bootstrap_remains_infra_not_staging_migration(self):
        bootstrap = read_text("infra/postgres/init/001_bootstrap.sql")
        conventions = read_text("docs/POSTGRES_MIGRATION_CONVENTIONS.md")

        self.assertIn("CREATE EXTENSION IF NOT EXISTS unaccent;", bootstrap)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS pg_trgm;", bootstrap)
        self.assertIn("CREATE SCHEMA IF NOT EXISTS receita_staging;", bootstrap)
        self.assertIn("não é migration de produto", conventions)
        self.assertIn("YYYYMMDDHHMMSS_descriptive_slug.sql", conventions)
        self.assertIn("apps/api/prisma/migrations", conventions)

    def test_apply_script_tracks_migrations_by_version_and_checksum(self):
        script = read_text("scripts/apply_postgres_migrations.ps1")

        self.assertIn("schema_migrations", script)
        self.assertIn("checksum_sha256", script)
        self.assertIn("Get-FileHash -Algorithm SHA256", script)
        self.assertIn("ON_ERROR_STOP=1", script)
        self.assertIn("SKIP", script)
        self.assertIn("APPLIED", script)
        self.assertIn("YYYYMMDDHHMMSS_descriptive_slug.sql", script)

    def test_import_script_extracts_copies_and_runs_server_copy(self):
        script = read_text("scripts/import_postgres_staging_file.ps1")
        planner = read_text("scripts/plan_postgres_staging_import.py")

        self.assertIn("apply_postgres_migrations.ps1", script)
        self.assertIn("python -m zipfile -e", script)
        self.assertIn("docker compose cp", script)
        self.assertIn("psql", script)
        self.assertIn("Importação concluída", script)
        self.assertIn("build_staging_import_manifest", planner)
        self.assertIn("sys.path.insert", planner)

    def test_snapshot_import_script_loops_recognized_files(self):
        script = read_text("scripts/import_postgres_staging_snapshot.ps1")
        planner = read_text("scripts/plan_postgres_staging_snapshot.py")

        self.assertIn("plan_postgres_staging_snapshot.py", script)
        self.assertIn("import_postgres_staging_file.ps1", script)
        self.assertIn("Families", script)
        self.assertIn("Limit", script)
        self.assertIn("snapshot_manifests", planner)
        self.assertIn("FAMILY_ORDER", planner)


if __name__ == "__main__":
    unittest.main()
