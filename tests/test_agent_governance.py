import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    activate_agent_config,
    add_companies_to_list,
    agent_governance,
    create_agent_config,
    create_agent_simulation,
    create_leads_from_list,
    create_list,
    record_agent_cost,
    upsert_company,
)


class AgentGovernanceTest(unittest.TestCase):
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

    def seed_lead(self, conn):
        company_id = upsert_company(
            conn,
            {
                "cnpj": "66.777.888/0001-99",
                "legal_name": "SIGMA GOVERNANCA LTDA",
                "trade_name": "Sigma Gov",
                "status": "Ativa",
                "email": "comercial@sigmagov.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Florianopolis",
                "state": "SC",
                "capital_social": 190000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )
        lead_list = create_list(conn, "Lista Governanca", "Teste")
        add_companies_to_list(conn, lead_list["id"], [company_id])
        create_leads_from_list(conn, lead_list["id"], "teste governanca")
        return conn.execute("SELECT * FROM leads WHERE company_id = ?", (company_id,)).fetchone()["id"]

    def test_governance_creates_default_active_config(self):
        conn = connect()
        try:
            data = agent_governance(conn)
            self.assertEqual(data["active_config"]["version_number"], 1)
            self.assertEqual(data["active_config"]["status"], "active")
            self.assertEqual(len(data["versions"]), 1)
            self.assertEqual(data["cost_summary"]["total_calls"], 0)
        finally:
            conn.close()

    def test_create_and_activate_agent_config(self):
        conn = connect()
        try:
            agent_governance(conn)
            config = create_agent_config(
                conn,
                {
                    "name": "SDR conservador",
                    "model_name": "gpt-5-mini",
                    "prompt_text": "Priorizar ICP e pedir aprovacao humana.",
                    "rules": {"requires_human_approval": True, "hard_guards": ["suppression_check"]},
                },
            )
            self.assertEqual(config["status"], "staging")
            self.assertEqual(config["version_number"], 2)

            activated = activate_agent_config(conn, config["id"])
            self.assertEqual(activated["status"], "active")
            data = agent_governance(conn)
            archived = [item for item in data["versions"] if item["version_number"] == 1][0]
            self.assertEqual(archived["status"], "archived")
            self.assertEqual(data["active_config"]["id"], config["id"])
        finally:
            conn.close()

    def test_simulation_records_config_and_lead_context(self):
        conn = connect()
        try:
            lead_id = self.seed_lead(conn)
            config = create_agent_config(
                conn,
                {
                    "name": "SDR staging",
                    "model_name": "gpt-5-mini",
                    "prompt_text": "Simular primeiro contato.",
                    "rules": {"requires_human_approval": True, "hard_guards": ["icp_required"]},
                },
            )
            simulation = create_agent_simulation(
                conn,
                {"config_version_id": config["id"], "lead_id": lead_id, "scenario": "first_contact"},
            )
            self.assertEqual(simulation["status"], "completed")
            self.assertEqual(simulation["result"]["lead_id"], lead_id)
            self.assertEqual(simulation["result"]["decision"], "requires_human_review")
            self.assertIn("icp_required", simulation["result"]["hard_guards"])
        finally:
            conn.close()

    def test_agent_cost_summary_aggregates_tokens_and_cost(self):
        conn = connect()
        try:
            lead_id = self.seed_lead(conn)
            config = agent_governance(conn)["active_config"]
            record = record_agent_cost(
                conn,
                {
                    "config_version_id": config["id"],
                    "lead_id": lead_id,
                    "operation": "classify_reply",
                    "model_name": "gpt-5-mini",
                    "prompt_tokens": 500,
                    "completion_tokens": 120,
                    "estimated_cost": 0.012,
                },
            )
            self.assertEqual(record["total_tokens"], 620)
            summary = agent_governance(conn)["cost_summary"]
            self.assertEqual(summary["total_calls"], 1)
            self.assertEqual(summary["total_tokens"], 620)
            self.assertEqual(summary["estimated_cost"], 0.012)
            self.assertEqual(summary["by_model"][0]["model_name"], "gpt-5-mini")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
