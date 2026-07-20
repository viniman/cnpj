import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    apply_playbook,
    create_playbook,
    create_playbook_version,
    playbook_library,
)


class PlaybookLibraryTest(unittest.TestCase):
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

    def sample_content(self, state="SP", target=10):
        return {
            "icp": {"states": [state], "target_cnaes": ["620"], "min_email_score": 30},
            "copy": {"tone": "direto"},
            "cadence": {"steps": [{"name": "Primeiro contato", "wait_days": 0}]},
            "okr": {"objective": "Validar nicho", "key_results": [{"kpi_key": "replies_received", "target_value": target}]},
            "governance": {"requires_human_approval": True},
        }

    def test_library_creates_default_playbook_and_profile(self):
        conn = connect()
        try:
            data = playbook_library(conn)
            self.assertEqual(data["company_profile"]["display_name"], "Workspace interno")
            self.assertEqual(len(data["playbooks"]), 1)
            self.assertEqual(data["playbooks"][0]["name"], "Outbound B2B Servicos Locais")
            self.assertEqual(data["playbooks"][0]["active_version"]["version_number"], 1)
            self.assertIsNone(data["active_application"])
        finally:
            conn.close()

    def test_create_playbook_creates_active_version_one(self):
        conn = connect()
        try:
            playbook = create_playbook(
                conn,
                {
                    "name": "Outbound SaaS Sul",
                    "description": "Teste de software no Sul",
                    "content": self.sample_content("SC"),
                },
            )
            self.assertEqual(playbook["active_version"]["version_number"], 1)
            self.assertEqual(playbook["active_version"]["status"], "active")
            self.assertEqual(playbook["active_version"]["content"]["icp"]["states"], ["SC"])
        finally:
            conn.close()

    def test_create_playbook_version_archives_previous_active(self):
        conn = connect()
        try:
            playbook = create_playbook(
                conn,
                {"name": "Outbound Health", "description": "Clinicas", "content": self.sample_content("SP")},
            )
            version = create_playbook_version(
                conn,
                playbook["id"],
                {"description": "Ajuste PR", "content": self.sample_content("PR", target=15)},
            )
            self.assertEqual(version["version_number"], 2)
            updated = playbook_library(conn)["playbooks"][0]
            versions = sorted(updated["versions"], key=lambda item: item["version_number"])
            self.assertEqual(versions[0]["status"], "archived")
            self.assertEqual(versions[1]["status"], "active")
            self.assertEqual(updated["active_version"]["content"]["icp"]["states"], ["PR"])
        finally:
            conn.close()

    def test_apply_playbook_sets_active_application(self):
        conn = connect()
        try:
            playbook = create_playbook(
                conn,
                {"name": "Outbound Local", "description": "Servicos", "content": self.sample_content("SP")},
            )
            application = apply_playbook(conn, playbook["id"], {"note": "Aplicar no workspace"})
            self.assertEqual(application["status"], "active")
            self.assertEqual(application["playbook_id"], playbook["id"])
            self.assertEqual(application["version_number"], 1)
            self.assertEqual(application["note"], "Aplicar no workspace")
            library = playbook_library(conn)
            self.assertEqual(library["active_application"]["id"], application["id"])
            self.assertEqual(library["active_application"]["content"]["icp"]["states"], ["SP"])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
