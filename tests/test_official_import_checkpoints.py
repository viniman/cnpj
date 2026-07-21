import os
import tempfile
import unittest
import zipfile

from radar_cnpj.database import connect, init_db
from radar_cnpj import official_sources
from radar_cnpj.services import (
    get_official_import_checkpoint,
    import_official_zip_directory,
    list_official_import_checkpoints,
    record_official_import_checkpoint,
    search_companies,
)


def write_zip_csv(path, rows):
    content = "\n".join(";".join(row) for row in rows) + "\n"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(os.path.basename(path).replace(".zip", ".CSV"), content.encode("latin-1"))


def establishment_row(root, trade_name, email):
    row = [""] * 28
    row[0] = root
    row[1] = "0001"
    row[2] = "00"
    row[3] = "1"
    row[4] = trade_name
    row[5] = "02"
    row[6] = "20240101"
    row[10] = "20200101"
    row[11] = "6201501"
    row[13] = "RUA"
    row[14] = "CENTRAL"
    row[15] = "100"
    row[17] = "CENTRO"
    row[18] = "01000000"
    row[19] = "SP"
    row[20] = "3550308"
    row[21] = "11"
    row[22] = "30000000"
    row[27] = email
    return row


def build_official_zip_fixture(directory):
    write_zip_csv(os.path.join(directory, "Cnaes.zip"), [["6201501", "Desenvolvimento de software"]])
    write_zip_csv(os.path.join(directory, "Municipios.zip"), [["3550308", "SAO PAULO"]])
    write_zip_csv(os.path.join(directory, "Naturezas.zip"), [["2062", "Sociedade Empresaria Limitada"]])
    write_zip_csv(
        os.path.join(directory, "Empresas1.zip"),
        [
            ["11111111", "ALFA SOFTWARE LTDA", "2062", "", "10000,00", "01", ""],
            ["22222222", "BETA DADOS LTDA", "2062", "", "20000,00", "03", ""],
        ],
    )
    write_zip_csv(
        os.path.join(directory, "Estabelecimentos1.zip"),
        [
            establishment_row("11111111", "ALFA", "contato@alfa.com.br"),
            establishment_row("22222222", "BETA", "contato@beta.com.br"),
        ],
    )


class OfficialImportCheckpointTest(unittest.TestCase):
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

    def test_official_import_checkpoint_resumes_batches(self):
        fixture_dir = os.path.join(self.temp_dir.name, "receita")
        os.makedirs(fixture_dir, exist_ok=True)
        build_official_zip_fixture(fixture_dir)

        with connect() as conn:
            first = import_official_zip_directory(
                conn,
                fixture_dir,
                source_name="Receita teste",
                source_url="fixture",
                legal_basis="Teste automatizado",
                chunk=1,
                limit=1,
                offset=0,
            )
            first_checkpoint = record_official_import_checkpoint(conn, "2026-06", 1, first, 1)

            self.assertEqual(first_checkpoint["status"], "pending")
            self.assertEqual(first_checkpoint["next_offset"], 1)
            self.assertEqual(first_checkpoint["imported_rows"], 1)

            second = import_official_zip_directory(
                conn,
                fixture_dir,
                source_name="Receita teste",
                source_url="fixture",
                legal_basis="Teste automatizado",
                chunk=1,
                limit=1,
                offset=first_checkpoint["next_offset"],
            )
            second_checkpoint = record_official_import_checkpoint(conn, "2026-06", 1, second, 1)

            self.assertEqual(second_checkpoint["status"], "pending")
            self.assertEqual(second_checkpoint["next_offset"], 2)
            self.assertEqual(second_checkpoint["imported_rows"], 2)

            final = import_official_zip_directory(
                conn,
                fixture_dir,
                source_name="Receita teste",
                source_url="fixture",
                legal_basis="Teste automatizado",
                chunk=1,
                limit=1,
                offset=second_checkpoint["next_offset"],
            )
            final_checkpoint = record_official_import_checkpoint(conn, "2026-06", 1, final, 1)

            self.assertEqual(final_checkpoint["status"], "completed")
            self.assertEqual(final_checkpoint["next_offset"], 2)
            self.assertEqual(final_checkpoint["imported_rows"], 2)
            self.assertEqual(get_official_import_checkpoint(conn, "2026-06", 1)["id"], final_checkpoint["id"])
            self.assertEqual(list_official_import_checkpoints(conn)["items"][0]["status"], "completed")
            self.assertEqual(search_companies(conn, {"state": "SP"})["total"], 2)

    def test_sync_official_snapshot_resume_uses_checkpoint_offset(self):
        fixture_dir = os.path.join(self.temp_dir.name, "receita-sync")
        os.makedirs(fixture_dir, exist_ok=True)
        build_official_zip_fixture(fixture_dir)
        original_list_snapshot_files = official_sources.list_snapshot_files
        original_download_files = official_sources.download_files
        original_local_snapshot_dir = official_sources.local_snapshot_dir
        try:
            official_sources.list_snapshot_files = lambda snapshot: [
                {"name": "Cnaes.zip", "size_bytes": 1},
                {"name": "Municipios.zip", "size_bytes": 1},
                {"name": "Naturezas.zip", "size_bytes": 1},
                {"name": "Empresas1.zip", "size_bytes": 1},
                {"name": "Estabelecimentos1.zip", "size_bytes": 1},
                {"name": "Socios1.zip", "size_bytes": 1},
            ]
            official_sources.download_files = lambda conn, snapshot, filenames, force=False: [
                {"filename": filename, "path": os.path.join(fixture_dir, filename), "cached": True}
                for filename in filenames
            ]
            official_sources.local_snapshot_dir = lambda snapshot: fixture_dir

            with connect() as conn:
                first = official_sources.sync_official_snapshot(
                    conn,
                    snapshot="2026-06",
                    chunk=1,
                    limit=1,
                    mode="chunk",
                )
                second = official_sources.sync_official_snapshot(
                    conn,
                    snapshot="2026-06",
                    chunk=1,
                    limit=1,
                    mode="chunk",
                    resume=True,
                )

                self.assertEqual(first["imported"]["offset"], 0)
                self.assertEqual(first["checkpoint"]["next_offset"], 1)
                self.assertEqual(second["imported"]["offset"], 1)
                self.assertEqual(second["checkpoint"]["next_offset"], 2)
                self.assertEqual(second["checkpoint"]["imported_rows"], 2)
        finally:
            official_sources.list_snapshot_files = original_list_snapshot_files
            official_sources.download_files = original_download_files
            official_sources.local_snapshot_dir = original_local_snapshot_dir


if __name__ == "__main__":
    unittest.main()
