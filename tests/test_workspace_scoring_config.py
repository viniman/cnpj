import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    create_workspace,
    get_workspace_scoring_config,
    score_email_record,
    set_current_workspace,
    update_workspace_scoring_config,
)


class WorkspaceScoringConfigTest(unittest.TestCase):
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

    def test_default_scoring_config_is_created_for_workspace(self):
        with connect() as conn:
            config = get_workspace_scoring_config(conn)

            self.assertEqual(config["org_id"], 1)
            self.assertEqual(config["status"], "active")
            self.assertIn("rh", config["email_prefix_rules"])
            self.assertEqual(config["email_prefix_rules"]["rh"]["score"], 35)
            self.assertGreater(config["prefix_count"], 10)

    def test_custom_prefix_rule_changes_persisted_email_score(self):
        with connect() as conn:
            update_workspace_scoring_config(
                conn,
                {
                    "name": "Scoring RH",
                    "email_prefix_rules": {
                        "rh": {"area": "decisor de recursos humanos", "score": 82, "label": "decision_maker"}
                    },
                },
            )

            result = score_email_record(conn, "rh@empresa.com.br")

            self.assertEqual(result["score"], 82)
            self.assertEqual(result["classification"], "decision_maker")
            self.assertEqual(result["scoring_config_name"], "Scoring RH")
            self.assertTrue(result["workspace_prefix_rules_applied"])
            self.assertIn("Regra de prefixo do workspace aplicada", result["reasons"])
            saved = conn.execute(
                "SELECT classification, score, reasons_json FROM email_classifications WHERE email = ? ORDER BY id DESC LIMIT 1",
                ("rh@empresa.com.br",),
            ).fetchone()
            self.assertEqual(saved["classification"], "decision_maker")
            self.assertEqual(saved["score"], 82)
            self.assertIn("Regra de prefixo do workspace aplicada", saved["reasons_json"])

    def test_scoring_config_does_not_cross_workspaces(self):
        with connect() as conn:
            update_workspace_scoring_config(
                conn,
                {"email_prefix_rules": {"rh": {"area": "decisor RH", "score": 82, "label": "decision_maker"}}},
            )
            internal_result = score_email_record(conn, "rh@empresa.com.br")

            workspace = create_workspace(conn, {"name": "Nine Scoring"})
            set_current_workspace(conn, workspace["id"])
            scoped_config = get_workspace_scoring_config(conn)
            scoped_result = score_email_record(conn, "rh@empresa.com.br")

            self.assertEqual(internal_result["score"], 82)
            self.assertEqual(scoped_config["org_id"], workspace["id"])
            self.assertEqual(scoped_config["email_prefix_rules"]["rh"]["score"], 35)
            self.assertEqual(scoped_result["score"], 35)
            self.assertNotEqual(scoped_result["scoring_config_id"], internal_result["scoring_config_id"])

    def test_invalid_prefix_score_is_rejected(self):
        with connect() as conn:
            with self.assertRaises(ValueError):
                update_workspace_scoring_config(conn, {"email_prefix_rules": {"rh": {"score": 120}}})


if __name__ == "__main__":
    unittest.main()
