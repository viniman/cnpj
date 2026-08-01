import os
import tempfile
import unittest
import zipfile

from scripts.plan_postgres_staging_snapshot import snapshot_manifests


def write_zip(path, member_name, content="1;Teste\n"):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member_name, content.encode("latin-1"))


class PostgresSnapshotPlanTest(unittest.TestCase):
    def test_snapshot_manifests_filters_and_orders_official_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_zip(os.path.join(temp_dir, "Socios1.zip"), "Socios1.CSV")
            write_zip(os.path.join(temp_dir, "Empresas0.zip"), "Empresas0.CSV")
            write_zip(os.path.join(temp_dir, "Cnaes.zip"), "Cnaes.CSV")
            write_zip(os.path.join(temp_dir, "LeiaMe.zip"), "LeiaMe.txt")

            manifests = snapshot_manifests("2026-07", temp_dir)

        self.assertEqual([item["filename"] for item in manifests], ["Cnaes.zip", "Empresas0.zip", "Socios1.zip"])
        self.assertEqual(manifests[0]["family"], "cnaes")
        self.assertGreater(manifests[0]["zip_size_bytes"], 0)
        self.assertEqual(manifests[1]["chunk"], 0)
        self.assertIn("COPY tmp_receita_empresas_import", manifests[1]["import_sql"])
        self.assertIn("DELETE FROM receita_staging.empresas_raw", manifests[1]["import_sql"])

    def test_snapshot_manifests_filters_families_and_limit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_zip(os.path.join(temp_dir, "Empresas0.zip"), "Empresas0.CSV")
            write_zip(os.path.join(temp_dir, "Empresas1.zip"), "Empresas1.CSV")
            write_zip(os.path.join(temp_dir, "Socios0.zip"), "Socios0.CSV")

            manifests = snapshot_manifests("2026-07", temp_dir, families=["empresas"], limit=1)

        self.assertEqual(len(manifests), 1)
        self.assertEqual(manifests[0]["filename"], "Empresas0.zip")


if __name__ == "__main__":
    unittest.main()
