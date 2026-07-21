import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    apply_playbook,
    audit_events,
    clone_playbook_to_workspace,
    create_playbook,
    create_playbook_version,
    create_workspace,
    get_playbook,
    playbook_library,
    set_current_workspace,
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

            second = playbook_library(conn)
            self.assertEqual(len(second["playbooks"]), 1)
            created = create_playbook(
                conn,
                {"name": "Depois do default", "description": "Idempotencia", "content": self.sample_content("RJ")},
            )
            self.assertEqual(created["active_version"]["version_number"], 1)
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

    def test_playbooks_follow_active_workspace(self):
        conn = connect()
        try:
            internal_library = playbook_library(conn)
            internal_default_id = internal_library["playbooks"][0]["id"]
            internal_playbook = create_playbook(
                conn,
                {"name": "Playbook compartilhavel", "description": "Interno", "content": self.sample_content("SP")},
            )
            internal_application = apply_playbook(conn, internal_playbook["id"], {"note": "Aplicacao interna"})

            workspace = create_workspace(conn, {"name": "Nine Playbooks"})
            set_current_workspace(conn, workspace["id"])

            scoped_empty = playbook_library(conn)
            self.assertEqual(scoped_empty["company_profile"]["org_id"], workspace["id"])
            self.assertEqual(len(scoped_empty["playbooks"]), 1)
            self.assertEqual(scoped_empty["playbooks"][0]["name"], "Outbound B2B Servicos Locais")
            self.assertEqual(scoped_empty["active_application"], None)
            self.assertIsNone(get_playbook(conn, internal_default_id))
            self.assertIsNone(get_playbook(conn, internal_playbook["id"]))
            with self.assertRaises(ValueError):
                create_playbook_version(conn, internal_playbook["id"], {"content": self.sample_content("RJ")})
            with self.assertRaises(ValueError):
                apply_playbook(conn, internal_playbook["id"], {"note": "Nao deveria cruzar"})

            scoped_playbook = create_playbook(
                conn,
                {"name": "Playbook compartilhavel", "description": "Nine", "content": self.sample_content("SC")},
            )
            scoped_version = create_playbook_version(
                conn,
                scoped_playbook["id"],
                {"description": "Ajuste Nine", "content": self.sample_content("PR")},
            )
            scoped_application = apply_playbook(
                conn,
                scoped_playbook["id"],
                {"version_id": scoped_version["id"], "note": "Aplicacao Nine"},
            )
            self.assertEqual(scoped_playbook["org_id"], workspace["id"])
            self.assertEqual(scoped_application["org_id"], workspace["id"])
            self.assertEqual(scoped_application["content"]["icp"]["states"], ["PR"])

            set_current_workspace(conn, 1)
            restored = playbook_library(conn)
            self.assertEqual(restored["active_application"]["id"], internal_application["id"])
            self.assertEqual(restored["active_application"]["note"], "Aplicacao interna")
            self.assertIsNone(get_playbook(conn, scoped_playbook["id"]))
            with self.assertRaises(ValueError):
                apply_playbook(conn, scoped_playbook["id"], {"note": "Nao deveria voltar"})
        finally:
            conn.close()

    def test_clone_playbook_to_workspace_is_explicit_and_isolated(self):
        conn = connect()
        try:
            source_playbook = create_playbook(
                conn,
                {"name": "Playbook que converteu", "description": "Origem", "content": self.sample_content("SP")},
            )
            source_version = create_playbook_version(
                conn,
                source_playbook["id"],
                {"description": "Versao MG", "content": self.sample_content("MG", target=25)},
            )
            target = create_workspace(conn, {"name": "Destino Playbook"})

            clone = clone_playbook_to_workspace(
                conn,
                source_playbook["id"],
                {
                    "target_org_id": target["id"],
                    "version_id": source_version["id"],
                    "name": "Playbook clonado para destino",
                    "description": "Clone auditavel",
                },
            )
            self.assertEqual(clone["org_id"], target["id"])
            self.assertEqual(clone["source"], "cloned")
            self.assertEqual(clone["active_version"]["version_number"], 1)
            self.assertEqual(clone["active_version"]["content"]["icp"]["states"], ["MG"])
            self.assertIsNone(get_playbook(conn, clone["id"]))
            self.assertTrue(
                any(item["action"] == "clone_playbook_to_workspace" for item in audit_events(conn))
            )

            with self.assertRaises(ValueError):
                clone_playbook_to_workspace(conn, source_playbook["id"], {"target_org_id": 1})
            with self.assertRaises(ValueError):
                clone_playbook_to_workspace(conn, source_playbook["id"], {"target_org_id": 999})

            set_current_workspace(conn, target["id"])
            cloned_in_target = get_playbook(conn, clone["id"])
            self.assertEqual(cloned_in_target["name"], "Playbook clonado para destino")
            self.assertEqual(playbook_library(conn)["active_application"], None)
            self.assertTrue(
                any(item["action"] == "receive_cloned_playbook" for item in audit_events(conn))
            )
            with self.assertRaises(ValueError):
                clone_playbook_to_workspace(conn, source_playbook["id"], {"target_org_id": 1})
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
