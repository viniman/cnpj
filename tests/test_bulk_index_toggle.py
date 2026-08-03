import os
import tempfile
import unittest

from scripts.bulk_index_toggle import (
    BULK_LOAD_TABLES,
    MIGRATION_PATH,
    create_sql,
    drop_sql,
    parse_bulk_load_indexes,
)

SAMPLE_MIGRATION = """
CREATE TABLE IF NOT EXISTS receita_staging.empresas_raw (
    cnpj_basico text
);

CREATE INDEX IF NOT EXISTS idx_receita_empresas_cnpj_basico ON receita_staging.empresas_raw (cnpj_basico);
CREATE INDEX IF NOT EXISTS idx_receita_empresas_razao_trgm ON receita_staging.empresas_raw USING gin (razao_social gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_receita_estab_cnpj_completo ON receita_staging.estabelecimentos_raw ((cnpj_basico || cnpj_ordem || cnpj_dv));
CREATE INDEX IF NOT EXISTS idx_receita_cnaes_codigo ON receita_staging.cnaes_raw (codigo);
"""


class BulkIndexToggleTest(unittest.TestCase):
    def test_parses_only_requested_big_tables(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sql", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(SAMPLE_MIGRATION)
            path = handle.name

        try:
            indexes = parse_bulk_load_indexes(
                migration_path=path, tables={"empresas_raw", "estabelecimentos_raw"}
            )
        finally:
            os.remove(path)

        names = sorted(index["name"] for index in indexes)
        self.assertEqual(
            names,
            [
                "idx_receita_empresas_cnpj_basico",
                "idx_receita_empresas_razao_trgm",
                "idx_receita_estab_cnpj_completo",
            ],
        )
        self.assertNotIn("idx_receita_cnaes_codigo", names)

    def test_drop_sql_targets_each_index_by_schema_qualified_name(self):
        indexes = [
            {"name": "idx_a", "table": "empresas_raw", "create_sql": "CREATE INDEX ..."},
            {"name": "idx_b", "table": "empresas_raw", "create_sql": "CREATE INDEX ..."},
        ]
        sql = drop_sql(indexes)
        self.assertIn("DROP INDEX IF EXISTS receita_staging.idx_a;", sql)
        self.assertIn("DROP INDEX IF EXISTS receita_staging.idx_b;", sql)

    def test_create_sql_reuses_the_exact_statement_from_the_migration(self):
        indexes = parse_bulk_load_indexes(tables={"empresas_raw"})
        sql = create_sql(indexes)
        for index in indexes:
            self.assertIn(index["create_sql"], sql)

    def test_real_migration_file_exposes_the_three_expensive_trgm_indexes(self):
        indexes = parse_bulk_load_indexes(
            migration_path=MIGRATION_PATH, tables=BULK_LOAD_TABLES
        )
        trgm_indexes = [index for index in indexes if "trgm" in index["name"]]
        self.assertEqual(len(trgm_indexes), 3)
        self.assertEqual(len(indexes), 9)


if __name__ == "__main__":
    unittest.main()
