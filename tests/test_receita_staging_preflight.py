import os
import tempfile
import unittest
import zipfile

from scripts.plan_receita_staging_preflight import disk_capacity_check, preflight_report, recognized_zip_files


def write_zip(path, member_name, content="1;Teste\n"):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member_name, content.encode("latin-1"))


class ReceitaStagingPreflightTest(unittest.TestCase):
    def test_recognized_zip_files_separates_official_and_ignored_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_zip(os.path.join(temp_dir, "Cnaes.zip"), "Cnaes.CSV")
            write_zip(os.path.join(temp_dir, "Empresas0.zip"), "Empresas0.CSV")
            write_zip(os.path.join(temp_dir, "LeiaMe.zip"), "LeiaMe.txt")

            files, ignored = recognized_zip_files(temp_dir)

        self.assertEqual([item["filename"] for item in files], ["Cnaes.zip", "Empresas0.zip"])
        self.assertEqual(ignored, ["LeiaMe.zip"])

    def test_preflight_fails_when_snapshot_directory_is_missing(self):
        report = preflight_report("2026-07", os.path.join("missing", "snapshot"))

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["checks"][0]["name"], "source_dir")
        self.assertIn("Snapshot directory not found", report["checks"][0]["message"])

    def test_preflight_passes_scoped_smoke_subset_with_expected_count_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_zip(os.path.join(temp_dir, "Cnaes.zip"), "Cnaes.CSV")
            write_zip(os.path.join(temp_dir, "Municipios.zip"), "Municipios.CSV")
            write_zip(os.path.join(temp_dir, "Naturezas.zip"), "Naturezas.CSV")

            report = preflight_report(
                "2026-07",
                temp_dir,
                families=["cnaes", "municipios", "naturezas"],
                limit=3,
                expected_files=3,
                free_bytes=1,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["recognized_files"], 3)
        self.assertIn("smoke_import", report["next_commands"])
        self.assertIn("-Families cnaes,municipios,naturezas", report["next_commands"]["smoke_import"])
        planner_check = next(check for check in report["checks"] if check["name"] == "snapshot_planner")
        self.assertEqual(planner_check["status"], "pass")
        disk_check = next(check for check in report["checks"] if check["name"] == "disk_capacity")
        self.assertEqual(disk_check["status"], "pass")

    def test_preflight_warns_when_count_differs_but_required_families_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for name in [
                "Cnaes.zip",
                "Motivos.zip",
                "Municipios.zip",
                "Naturezas.zip",
                "Paises.zip",
                "Qualificacoes.zip",
                "Simples.zip",
                "Empresas0.zip",
                "Estabelecimentos0.zip",
                "Socios0.zip",
            ]:
                write_zip(os.path.join(temp_dir, name), name.replace(".zip", ".CSV"))

            report = preflight_report("2026-07", temp_dir, expected_files=37, free_bytes=10**12)

        self.assertEqual(report["status"], "warn")
        count_check = next(check for check in report["checks"] if check["name"] == "expected_file_count")
        self.assertEqual(count_check["status"], "warn")

    def test_disk_capacity_fails_full_import_when_free_space_is_too_low(self):
        check = disk_capacity_check(total_bytes=100, free_bytes=199, multiplier=2.0, scoped=False)

        self.assertEqual(check["status"], "fail")
        self.assertEqual(check["details"]["required_bytes"], 200)

    def test_preflight_fails_full_import_when_disk_capacity_is_low(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for name in [
                "Cnaes.zip",
                "Motivos.zip",
                "Municipios.zip",
                "Naturezas.zip",
                "Paises.zip",
                "Qualificacoes.zip",
                "Simples.zip",
                "Empresas0.zip",
                "Estabelecimentos0.zip",
                "Socios0.zip",
            ]:
                write_zip(os.path.join(temp_dir, name), name.replace(".zip", ".CSV"))

            report = preflight_report("2026-07", temp_dir, expected_files=10, free_bytes=1, disk_multiplier=2.0)

        self.assertEqual(report["status"], "fail")
        disk_check = next(check for check in report["checks"] if check["name"] == "disk_capacity")
        self.assertEqual(disk_check["status"], "fail")


if __name__ == "__main__":
    unittest.main()
