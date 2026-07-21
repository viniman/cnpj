import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    apply_playbook_execution_plan,
    create_playbook,
    create_playbook_execution_plan,
    create_playbook_version,
    create_workspace,
    list_email_templates,
    list_icp_rules,
    list_playbook_execution_plans,
    list_sequences,
    okr_dashboard,
    set_current_workspace,
)


class PlaybookExecutionPlanTest(unittest.TestCase):
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

    def sample_content(self, state="SP"):
        return {
            "icp": {"states": [state], "target_cnaes": ["620"], "min_email_score": 40},
            "copy": {"tone": "direto"},
            "cadence": {
                "steps": [
                    {"name": "Primeiro contato", "wait_days": 0},
                    {"name": "Follow-up", "wait_days": 4},
                ]
            },
            "okr": {
                "objective": "Validar plano",
                "key_results": [{"title": "Receber respostas", "kpi_key": "replies_received", "target_value": 8}],
            },
        }

    def test_execution_plan_previews_before_apply(self):
        conn = connect()
        try:
            playbook = create_playbook(
                conn,
                {"name": "Plano Playbook", "description": "Preview", "content": self.sample_content("SP")},
            )
            plan = create_playbook_execution_plan(conn, playbook["id"], {})

            self.assertEqual(plan["status"], "draft")
            self.assertEqual(plan["playbook_id"], playbook["id"])
            self.assertEqual(plan["plan"]["icp_rule"]["criteria"]["states"], ["SP"])
            self.assertEqual(len(plan["plan"]["sequence"]["steps"]), 2)
            self.assertEqual(plan["diff"]["current_counts"]["icp_rules"], 0)
            self.assertEqual(list_icp_rules(conn)["items"], [])
            self.assertEqual(list_email_templates(conn)["items"], [])
            self.assertEqual(list_sequences(conn)["items"], [])
            self.assertEqual(okr_dashboard(conn)["objectives"][0]["id"], "default")

            listed = list_playbook_execution_plans(conn)["items"]
            self.assertEqual([item["id"] for item in listed], [plan["id"]])
        finally:
            conn.close()

    def test_apply_execution_plan_creates_artifacts_once(self):
        conn = connect()
        try:
            playbook = create_playbook(
                conn,
                {"name": "Aplicar Plano", "description": "Aplicacao", "content": self.sample_content("RJ")},
            )
            plan = create_playbook_execution_plan(conn, playbook["id"], {})
            applied = apply_playbook_execution_plan(conn, plan["id"], {"note": "Aprovado pelo teste"})

            self.assertEqual(applied["status"], "applied")
            self.assertEqual(applied["created"]["active_application"]["playbook_id"], playbook["id"])
            self.assertEqual(applied["created"]["icp_rule"]["criteria"]["states"], ["RJ"])
            self.assertEqual(applied["created"]["template"]["active_version"]["version_number"], 1)
            self.assertEqual(len(applied["created"]["sequence"]["steps"]), 2)
            self.assertTrue(all(step["require_approval"] == 1 for step in applied["created"]["sequence"]["steps"]))
            self.assertEqual(applied["created"]["objective"]["title"], "Validar plano")
            self.assertEqual(applied["created_artifacts"]["icp_rule_id"], applied["created"]["icp_rule"]["id"])

            with self.assertRaises(ValueError):
                apply_playbook_execution_plan(conn, plan["id"], {})
        finally:
            conn.close()

    def test_execution_plan_follows_active_workspace(self):
        conn = connect()
        try:
            internal_playbook = create_playbook(
                conn,
                {"name": "Plano interno", "description": "Interno", "content": self.sample_content("SP")},
            )
            internal_plan = create_playbook_execution_plan(conn, internal_playbook["id"], {})
            workspace = create_workspace(conn, {"name": "Workspace Plano"})
            set_current_workspace(conn, workspace["id"])

            self.assertEqual(list_playbook_execution_plans(conn)["items"], [])
            with self.assertRaises(ValueError):
                create_playbook_execution_plan(conn, internal_playbook["id"], {})
            with self.assertRaises(ValueError):
                apply_playbook_execution_plan(conn, internal_plan["id"], {})

            scoped_playbook = create_playbook(
                conn,
                {"name": "Plano scoped", "description": "Scoped", "content": self.sample_content("MG")},
            )
            scoped_version = create_playbook_version(
                conn,
                scoped_playbook["id"],
                {"description": "Versao PR", "content": self.sample_content("PR")},
            )
            scoped_plan = create_playbook_execution_plan(
                conn,
                scoped_playbook["id"],
                {"version_id": scoped_version["id"]},
            )
            self.assertEqual(scoped_plan["org_id"], workspace["id"])
            self.assertEqual(scoped_plan["plan"]["icp_rule"]["criteria"]["states"], ["PR"])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
