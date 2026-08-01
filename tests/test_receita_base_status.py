import os
import tempfile
import unittest
import zipfile

from scripts.plan_receita_base_status import build_base_status, status_from_preflight


def write_zip(path, member_name, content="1;Teste\n"):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member_name, content.encode("latin-1"))


class ReceitaBaseStatusTest(unittest.TestCase):
    def test_status_from_preflight_detects_disk_blocker(self):
        status = status_from_preflight(
            {
                "status": "fail",
                "checks": [{"name": "disk_capacity", "status": "fail"}],
            }
        )

        self.assertEqual(status, "blocked_disk")

    def test_build_base_status_reports_next_gate_and_commands(self):
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

            report = build_base_status("2026-07", temp_dir, free_bytes=1, disk_multiplier=2.0)

        self.assertEqual(report["status"], "blocked_disk")
        self.assertEqual(report["next_gate"]["key"], "disk_capacity")
        self.assertIn("smoke_counts", report["commands"])
        self.assertEqual(report["preflight"]["recognized_files"], 10)


if __name__ == "__main__":
    unittest.main()
