import json
import os
import tempfile
import threading
import unittest
import zipfile
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from radar_cnpj.database import connect, init_db, now_iso
from radar_cnpj.postgres_staging import (
    build_server_import_sql,
    build_postgres_staging_plan,
    build_staging_import_manifest,
    official_file_family,
    postgres_staging_schema,
)
from radar_cnpj.server import RadarHandler


def write_zip(path, member_name, content="1;Teste\n"):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member_name, content.encode("latin-1"))


class PostgresStagingTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db = os.environ.get("RADAR_CNPJ_DB")
        os.environ["RADAR_CNPJ_DB"] = os.path.join(self.temp_dir.name, "test.sqlite")
        init_db()

    def tearDown(self):
        if self.old_db is None:
            os.environ.pop("RADAR_CNPJ_DB", None)
        else:
            os.environ["RADAR_CNPJ_DB"] = self.old_db
        self.temp_dir.cleanup()

    def test_official_file_family_detects_chunked_and_domain_files(self):
        empresas = official_file_family("Empresas1.zip")
        cnaes = official_file_family("Cnaes.zip")

        self.assertEqual(empresas["family"], "empresas")
        self.assertEqual(empresas["chunk"], 1)
        self.assertEqual(empresas["table"], "empresas_raw")
        self.assertIn("razao_social", empresas["columns"])
        self.assertEqual(cnaes["family"], "cnaes")
        self.assertIsNone(cnaes["chunk"])
        self.assertIsNone(official_file_family("LeiaMe.txt"))

    def test_postgres_staging_schema_contains_extensions_tables_and_indexes(self):
        sql = postgres_staging_schema()

        self.assertIn("CREATE EXTENSION IF NOT EXISTS unaccent;", sql)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS pg_trgm;", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS receita_staging.estabelecimentos_raw", sql)
        self.assertIn("correio_eletronico text", sql)
        self.assertIn("idx_receita_estab_cnpj_completo", sql)
        self.assertIn("gin_trgm_ops", sql)

    def test_build_postgres_staging_plan_generates_copy_for_available_zip(self):
        zip_path = os.path.join(self.temp_dir.name, "Empresas1.zip")
        write_zip(zip_path, "Empresas1.CSV")

        plan = build_postgres_staging_plan(
            "2026-06",
            [
                {
                    "snapshot": "2026-06",
                    "filename": "Empresas1.zip",
                    "size_bytes": os.path.getsize(zip_path),
                    "local_path": zip_path,
                    "status": "downloaded",
                }
            ],
        )

        self.assertEqual(plan["summary"]["available_files"], 1)
        self.assertEqual(plan["copy_plan"][0]["family"], "empresas")
        self.assertEqual(plan["copy_plan"][0]["csv_member"], "Empresas1.CSV")
        self.assertIn("CREATE TEMP TABLE tmp_receita_empresas_import", plan["copy_plan"][0]["copy_sql"])
        self.assertIn("\\copy tmp_receita_empresas_import", plan["copy_plan"][0]["copy_sql"])
        self.assertIn("DELETE FROM receita_staging.empresas_raw", plan["copy_plan"][0]["copy_sql"])
        self.assertIn("ENCODING 'LATIN1'", plan["copy_plan"][0]["copy_sql"])
        self.assertIn("'2026-06'", plan["copy_plan"][0]["copy_sql"])
        self.assertIn("scripts\\import_postgres_staging_file.ps1", plan["copy_plan"][0]["import_command"])
        self.assertIn("-Filename 'Empresas1.zip'", plan["copy_plan"][0]["import_command"])
        self.assertIn("check_receita_staging_preflight.ps1", plan["commands"]["preflight"])
        self.assertIn("-SkipDockerCheck", plan["commands"]["preflight_without_docker"])
        self.assertIn("-Families cnaes,municipios,naturezas", plan["commands"]["smoke_import"])
        self.assertIn("import_postgres_staging_snapshot.ps1", plan["commands"]["snapshot_import"])
        self.assertIn("disk_capacity", plan)
        self.assertIn(plan["disk_capacity"]["status"], {"pass", "warn", "fail"})
        self.assertEqual(plan["summary"]["disk_capacity_status"], plan["disk_capacity"]["status"])
        self.assertIn("Estabelecimentos1.zip", {item["filename"] for item in plan["missing_files"]})

    def test_build_server_import_sql_uses_temp_table_and_replace(self):
        sql = build_server_import_sql("2026-07", "Cnaes.zip", "/tmp/radar-cnpj-staging/Cnaes/Cnaes.CSV")

        self.assertIn("CREATE TEMP TABLE tmp_receita_cnaes_import", sql)
        self.assertIn("COPY tmp_receita_cnaes_import", sql)
        self.assertIn("FROM '/tmp/radar-cnpj-staging/Cnaes/Cnaes.CSV'", sql)
        self.assertIn("ENCODING 'LATIN1'", sql)
        self.assertIn("DELETE FROM receita_staging.cnaes_raw WHERE snapshot = '2026-07'", sql)
        self.assertIn("INSERT INTO receita_staging.cnaes_raw", sql)
        self.assertIn("'Cnaes.zip'", sql)
        self.assertNotIn("WHERE source_file IS NULL", sql)

    def test_build_staging_import_manifest_extracts_zip_member_and_container_path(self):
        zip_path = os.path.join(self.temp_dir.name, "Cnaes.zip")
        write_zip(zip_path, "Cnaes.CSV")

        manifest = build_staging_import_manifest(
            "2026-07",
            "Cnaes.zip",
            zip_path=zip_path,
            extract_root=os.path.join(self.temp_dir.name, "extract"),
            container_dir="/tmp/radar-cnpj-staging",
        )

        self.assertEqual(manifest["family"], "cnaes")
        self.assertEqual(manifest["table"], "receita_staging.cnaes_raw")
        self.assertEqual(manifest["csv_member"], "Cnaes.CSV")
        self.assertTrue(manifest["local_csv_path"].endswith(os.path.join("Cnaes", "Cnaes.CSV")))
        self.assertEqual(manifest["container_csv_path"], "/tmp/radar-cnpj-staging/Cnaes/Cnaes.CSV")
        self.assertIn("COPY tmp_receita_cnaes_import", manifest["import_sql"])
        self.assertIn("DELETE FROM receita_staging.cnaes_raw", manifest["import_sql"])

    def test_postgres_plan_route_uses_downloaded_source_files(self):
        zip_path = os.path.join(self.temp_dir.name, "Cnaes.zip")
        write_zip(zip_path, "Cnaes.CSV")
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO source_files (
                    snapshot, filename, url, size_bytes, etag, local_path, status,
                    downloaded_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "2026-06",
                    "Cnaes.zip",
                    "https://example.test/Cnaes.zip",
                    os.path.getsize(zip_path),
                    "etag",
                    zip_path,
                    "downloaded",
                    now_iso(),
                    now_iso(),
                ),
            )
            conn.commit()

        server = ThreadingHTTPServer(("127.0.0.1", 0), RadarHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            url = f"http://127.0.0.1:{port}/api/sources/official/postgres-plan?snapshot=2026-06"
            with urlopen(url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            self.assertEqual(response.status, 200)
            self.assertEqual(payload["snapshot"], "2026-06")
            self.assertEqual(payload["summary"]["available_files"], 1)
            self.assertEqual(payload["copy_plan"][0]["table"], "receita_staging.cnaes_raw")
            self.assertIn("snapshot_import", payload["commands"])
            self.assertIn("disk_capacity", payload)
            self.assertIn("CREATE SCHEMA IF NOT EXISTS receita_staging", payload["ddl_sql"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
