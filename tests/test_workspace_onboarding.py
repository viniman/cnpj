import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    create_playbook,
    create_playbook_version,
    get_playbook,
    list_email_templates,
    list_icp_rules,
    list_cadences,
    okr_dashboard,
    playbook_library,
    run_workspace_onboarding,
    set_current_workspace,
    workspace_context,
)


class WorkspaceOnboardingTest(unittest.TestCase):
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
            "icp": {"states": [state], "target_cnaes": ["620"], "min_email_score": 35},
            "copy": {"tone": "consultivo"},
            "cadence": {
                "steps": [
                    {"name": "Primeiro contato", "wait_days": 0},
                    {"name": "Follow-up", "wait_days": 3},
                ]
            },
            "okr": {
                "objective": "Validar onboarding",
                "key_results": [{"title": "Receber respostas", "kpi_key": "replies_received", "target_value": 5}],
            },
            "governance": {"requires_human_approval": True},
        }

    def test_onboarding_creates_operational_workspace(self):
        conn = connect()
        try:
            result = run_workspace_onboarding(
                conn,
                {
                    "workspace": {
                        "name": "Nine Wizard",
                        "vertical": "servicos locais",
                        "default_tone": "direto e consultivo",
                        "sending_domain": "mail.nine.local",
                        "sender_name": "Time Nine",
                        "brand_color": "#117733",
                    },
                    "icp": {
                        "name": "ICP Nine Wizard",
                        "criteria": {"states": ["SP"], "cnaes": ["620"], "min_email_score": 45},
                    },
                    "template": {
                        "subject": "Ideia para {{nome_empresa}}",
                        "body": "Ola {{nome_contato}}, podemos conversar sobre {{cidade}}? CTA: {{cta_url}}",
                    },
                    "okr": {
                        "title": "Validar Nine Wizard",
                        "key_results": [{"title": "Criar handoffs", "kpi_key": "pending_handoffs", "target_value": 1}],
                    },
                },
            )
            workspace_id = result["workspace"]["id"]
            self.assertEqual(workspace_context(conn)["active_workspace"]["id"], workspace_id)
            self.assertEqual(result["profile"]["sending_domain"], "mail.nine.local")
            self.assertEqual(result["active_application"]["org_id"], workspace_id)
            self.assertEqual(result["icp_rule"]["org_id"], workspace_id)
            self.assertEqual(result["icp_rule"]["criteria"]["states"], ["SP"])
            self.assertEqual(result["icp_rule"]["criteria"]["min_email_score"], 45)
            self.assertEqual(result["template"]["org_id"], workspace_id)
            self.assertEqual(result["cadence"]["org_id"], workspace_id)
            self.assertTrue(all(step["require_approval"] == 1 for step in result["cadence"]["steps"]))
            self.assertEqual(result["objective"]["org_id"], workspace_id)
            self.assertEqual(result["onboarding_run"]["summary"]["org_id"], workspace_id)
            self.assertEqual(len(list_icp_rules(conn)["items"]), 1)
            self.assertEqual(len(list_email_templates(conn)["items"]), 1)
            self.assertEqual(len(list_cadences(conn)["items"]), 1)
            self.assertEqual(okr_dashboard(conn)["objectives"][0]["title"], "Validar Nine Wizard")
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM workspace_onboarding_runs WHERE org_id = ?",
                (workspace_id,),
            ).fetchone()
            self.assertEqual(row["total"], 1)
        finally:
            conn.close()

    def test_onboarding_can_start_from_cloned_playbook(self):
        conn = connect()
        try:
            source = create_playbook(
                conn,
                {"name": "Playbook origem wizard", "description": "Origem", "content": self.sample_content("SP")},
            )
            source_version = create_playbook_version(
                conn,
                source["id"],
                {"description": "Ajuste PR", "content": self.sample_content("PR")},
            )
            result = run_workspace_onboarding(
                conn,
                {
                    "workspace": {"name": "Vagou Wizard", "vertical": "recrutamento"},
                    "playbook": {
                        "source_playbook_id": source["id"],
                        "source_version_id": source_version["id"],
                        "name": "Clone Wizard Vagou",
                    },
                },
            )
            workspace_id = result["workspace"]["id"]
            self.assertEqual(result["playbook"]["org_id"], workspace_id)
            self.assertEqual(result["playbook"]["source"], "cloned")
            self.assertEqual(result["active_application"]["content"]["icp"]["states"], ["PR"])
            self.assertEqual(result["icp_rule"]["criteria"]["states"], ["PR"])
            self.assertEqual(len(result["cadence"]["steps"]), 2)
            self.assertTrue(result["onboarding_run"]["summary"]["used_cloned_playbook"])

            set_current_workspace(conn, 1)
            self.assertIsNone(get_playbook(conn, result["playbook"]["id"]))

            set_current_workspace(conn, workspace_id)
            library = playbook_library(conn)
            self.assertEqual(library["active_application"]["playbook_id"], result["playbook"]["id"])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
