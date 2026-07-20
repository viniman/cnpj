import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    add_companies_to_list,
    add_suppression,
    create_icp_rule,
    create_list,
    decide_priority_queue_item,
    list_agent_actions,
    list_priority_queue,
    prioritize_icp_rule,
    upsert_company,
)


class IcpPrioritizationTest(unittest.TestCase):
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

    def seed_icp_list(self, conn):
        companies = [
            {
                "cnpj": "11.222.333/0001-81",
                "legal_name": "ALFA SOFTWARE LTDA",
                "status": "Ativa",
                "email": "comercial@alfa.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Sao Paulo",
                "state": "SP",
                "capital_social": 200000,
            },
            {
                "cnpj": "22.333.444/0001-81",
                "legal_name": "BETA SOFTWARE RJ LTDA",
                "status": "Ativa",
                "email": "comercial@beta.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Rio de Janeiro",
                "state": "RJ",
                "capital_social": 200000,
            },
            {
                "cnpj": "33.444.555/0001-81",
                "legal_name": "GAMA SOFTWARE LTDA",
                "status": "Ativa",
                "email": "comercial@gama.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Sao Paulo",
                "state": "SP",
                "capital_social": 200000,
            },
        ]
        ids = [upsert_company(conn, item, "Teste", "fixture", "Teste automatizado") for item in companies]
        lead_list = create_list(conn, "Lista ICP", "Teste")
        add_companies_to_list(conn, lead_list["id"], ids)
        return lead_list["id"]

    def test_prioritize_icp_rule_only_suggests_matching_unsuppressed_leads(self):
        conn = connect()
        try:
            list_id = self.seed_icp_list(conn)
            add_suppression(conn, "comercial@gama.com.br", "nao contactar")
            rule = create_icp_rule(
                conn,
                {
                    "name": "Software SP",
                    "criteria": {
                        "states": ["SP"],
                        "cnaes": ["620"],
                        "min_email_score": 30,
                        "require_email": True,
                        "exclude_suppressed": True,
                        "max_leads": 10,
                    },
                },
            )
            result = prioritize_icp_rule(conn, rule["id"], list_id=list_id)
            self.assertEqual(result["summary"]["suggested"], 1)
            self.assertEqual(result["summary"]["blocked"], 2)

            items = list_priority_queue(conn, {"icp_rule_id": rule["id"]})["items"]
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["legal_name"], "ALFA SOFTWARE LTDA")
            self.assertIn("UF dentro do ICP: SP", items[0]["reason"]["matched"])
            self.assertFalse(items[0]["reason"]["blocked"])
        finally:
            conn.close()

    def test_decide_priority_queue_item_records_human_action(self):
        conn = connect()
        try:
            list_id = self.seed_icp_list(conn)
            rule = create_icp_rule(
                conn,
                {
                    "name": "Software SP",
                    "criteria": {"states": "SP", "cnaes": "620", "max_leads": 1},
                },
            )
            prioritize_icp_rule(conn, rule["id"], list_id=list_id)
            item = list_priority_queue(conn, {"icp_rule_id": rule["id"]})["items"][0]
            decided = decide_priority_queue_item(conn, item["id"], "accept", "Lead bom para cadencia")
            self.assertEqual(decided["status"], "accepted")
            self.assertEqual(decided["decision_note"], "Lead bom para cadencia")

            actions = list_agent_actions(conn)["items"]
            action_types = [action["action_type"] for action in actions]
            self.assertIn("icp_prioritized", action_types)
            self.assertIn("priority_accepted", action_types)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
