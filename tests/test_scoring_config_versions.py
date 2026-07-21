import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    create_workspace,
    get_workspace_company_score_config,
    get_workspace_scoring_config,
    list_workspace_score_config_versions,
    rollback_workspace_score_config_version,
    set_current_workspace,
    update_workspace_company_score_config,
    update_workspace_scoring_config,
)


class ScoringConfigVersionsTest(unittest.TestCase):
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

    def test_default_configs_create_version_one_for_email_and_company(self):
        with connect() as conn:
            email_config = get_workspace_scoring_config(conn)
            company_config = get_workspace_company_score_config(conn)
            versions = list_workspace_score_config_versions(conn)["items"]

            self.assertEqual(email_config["active_version"]["version_number"], 1)
            self.assertEqual(company_config["active_version"]["version_number"], 1)
            self.assertEqual(email_config["version_count"], 1)
            self.assertEqual(company_config["version_count"], 1)
            self.assertEqual({item["config_type"] for item in versions}, {"email", "company"})
            self.assertTrue(all(item["status"] == "active" for item in versions))

    def test_email_config_update_and_rollback_create_auditable_versions(self):
        with connect() as conn:
            default = get_workspace_scoring_config(conn)
            update_workspace_scoring_config(
                conn,
                {
                    "name": "Scoring RH",
                    "email_prefix_rules": {"rh": {"area": "decisor RH", "score": 82, "label": "decision_maker"}},
                    "change_note": "Valorizar RH",
                },
            )
            versions_after_update = list_workspace_score_config_versions(conn, {"type": "email"})["items"]
            original_version = [item for item in versions_after_update if item["version_number"] == 1][0]
            active_after_update = [item for item in versions_after_update if item["status"] == "active"][0]

            self.assertEqual(default["email_prefix_rules"]["rh"]["score"], 35)
            self.assertEqual(active_after_update["version_number"], 2)
            self.assertEqual(active_after_update["config"]["email_prefix_rules"]["rh"]["score"], 82)
            self.assertEqual(original_version["status"], "archived")

            rollback = rollback_workspace_score_config_version(conn, original_version["id"])
            restored = get_workspace_scoring_config(conn)
            versions_after_rollback = list_workspace_score_config_versions(conn, {"type": "email"})["items"]
            active_after_rollback = [item for item in versions_after_rollback if item["status"] == "active"][0]

            self.assertEqual(restored["email_prefix_rules"]["rh"]["score"], 35)
            self.assertEqual(rollback["active_version"]["version_number"], 3)
            self.assertEqual(active_after_rollback["version_number"], 3)
            self.assertEqual(active_after_rollback["change_note"], "Rollback para v1")
            self.assertEqual(len(versions_after_rollback), 3)

    def test_company_config_update_and_rollback_restore_rules(self):
        with connect() as conn:
            get_workspace_company_score_config(conn)
            update_workspace_company_score_config(
                conn,
                {
                    "name": "Score Saude",
                    "rules": {"sector_bonus": {"Saude": 30}},
                    "change_note": "Priorizar Saude",
                },
            )
            versions_after_update = list_workspace_score_config_versions(conn, {"type": "company"})["items"]
            original_version = [item for item in versions_after_update if item["version_number"] == 1][0]
            updated_config = get_workspace_company_score_config(conn)

            self.assertEqual(updated_config["rules"]["sector_bonus"]["Saude"], 30)
            self.assertEqual(updated_config["active_version"]["version_number"], 2)

            rollback_workspace_score_config_version(conn, original_version["id"], {"change_note": "Voltar default"})
            restored = get_workspace_company_score_config(conn)
            versions_after_rollback = list_workspace_score_config_versions(conn, {"type": "company"})["items"]
            active_after_rollback = [item for item in versions_after_rollback if item["status"] == "active"][0]

            self.assertEqual(restored["rules"]["sector_bonus"]["Saude"], 7)
            self.assertEqual(restored["active_version"]["version_number"], 3)
            self.assertEqual(active_after_rollback["change_note"], "Voltar default")

    def test_versions_do_not_cross_workspaces(self):
        with connect() as conn:
            update_workspace_scoring_config(
                conn,
                {"email_prefix_rules": {"rh": {"area": "decisor RH", "score": 82, "label": "decision_maker"}}},
            )
            internal_versions = list_workspace_score_config_versions(conn, {"type": "email"})["items"]
            internal_old_version = [item for item in internal_versions if item["version_number"] == 1][0]

            workspace = create_workspace(conn, {"name": "Nine Historico"})
            set_current_workspace(conn, workspace["id"])
            scoped_config = get_workspace_scoring_config(conn)
            scoped_versions = list_workspace_score_config_versions(conn, {"type": "email"})["items"]

            self.assertEqual(scoped_config["org_id"], workspace["id"])
            self.assertEqual(scoped_config["email_prefix_rules"]["rh"]["score"], 35)
            self.assertEqual(len(scoped_versions), 1)
            self.assertEqual(scoped_versions[0]["version_number"], 1)
            self.assertEqual(scoped_versions[0]["org_id"], workspace["id"])
            with self.assertRaises(ValueError):
                rollback_workspace_score_config_version(conn, internal_old_version["id"])


if __name__ == "__main__":
    unittest.main()
