import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    create_icp_rule,
    create_workspace,
    get_company,
    get_workspace_company_score_config,
    prioritize_icp_rule,
    rescore_workspace_companies,
    search_companies,
    set_current_workspace,
    update_workspace_company_score_config,
    upsert_company,
)


class WorkspaceCompanyScoreConfigTest(unittest.TestCase):
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

    def seed_health_company(self, conn):
        return upsert_company(
            conn,
            {
                "cnpj": "12.345.678/0001-90",
                "legal_name": "CLINICA ALFA LTDA",
                "status": "Ativa",
                "main_cnae_code": "8630503",
                "main_cnae_description": "Atividade medica ambulatorial",
                "city": "Sao Paulo",
                "state": "SP",
                "size": "DEMAIS",
                "capital_social": 0,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )

    def test_default_company_score_config_is_created_for_workspace(self):
        with connect() as conn:
            config = get_workspace_company_score_config(conn)

            self.assertEqual(config["org_id"], 1)
            self.assertEqual(config["status"], "active")
            self.assertEqual(config["rules"]["base_score"], 20)
            self.assertEqual(config["rules"]["sector_bonus"]["Saude"], 7)
            self.assertGreaterEqual(config["sector_count"], 4)

    def test_custom_sector_bonus_rescores_workspace_without_overwriting_base_score(self):
        with connect() as conn:
            company_id = self.seed_health_company(conn)
            base = get_company(conn, company_id)
            self.assertFalse(base["workspace_score_applied"])
            self.assertEqual(base["opportunity_score"], 53)

            update_workspace_company_score_config(
                conn,
                {
                    "name": "Score Saude",
                    "rules": {"sector_bonus": {"Saude": 30}},
                },
            )
            result = rescore_workspace_companies(conn, {"limit": 10})
            detail = get_company(conn, company_id)
            raw = conn.execute("SELECT opportunity_score FROM companies WHERE id = ?", (company_id,)).fetchone()
            search = search_companies(conn, {"min_score": 70, "limit": 10})

            self.assertEqual(result["scored"], 1)
            self.assertEqual(raw["opportunity_score"], 53)
            self.assertTrue(detail["workspace_score_applied"])
            self.assertEqual(detail["base_opportunity_score"], 53)
            self.assertEqual(detail["opportunity_score"], 76)
            self.assertEqual(detail["company_scoring_config_name"], "Score Saude")
            self.assertIn("+30 setor com boa aderencia B2B", detail["score_reasons"])
            self.assertEqual(search["total"], 1)
            self.assertEqual(search["items"][0]["opportunity_score"], 76)
            self.assertEqual(search["items"][0]["base_opportunity_score"], 53)

    def test_company_score_config_and_overlay_do_not_cross_workspaces(self):
        with connect() as conn:
            company_id = self.seed_health_company(conn)
            update_workspace_company_score_config(conn, {"rules": {"sector_bonus": {"Saude": 30}}})
            rescore_workspace_companies(conn, {"limit": 10})
            internal_detail = get_company(conn, company_id)

            workspace = create_workspace(conn, {"name": "Nine Score"})
            set_current_workspace(conn, workspace["id"])
            scoped_config = get_workspace_company_score_config(conn)
            scoped_detail = get_company(conn, company_id)
            scoped_search = search_companies(conn, {"min_score": 70, "limit": 10})

            self.assertEqual(internal_detail["opportunity_score"], 76)
            self.assertEqual(scoped_config["org_id"], workspace["id"])
            self.assertEqual(scoped_config["rules"]["sector_bonus"]["Saude"], 7)
            self.assertFalse(scoped_detail["workspace_score_applied"])
            self.assertEqual(scoped_detail["opportunity_score"], 53)
            self.assertEqual(scoped_search["total"], 0)

    def test_icp_prioritization_uses_workspace_company_score_overlay(self):
        with connect() as conn:
            self.seed_health_company(conn)
            rule = create_icp_rule(
                conn,
                {
                    "name": "Clinicas com score alto",
                    "criteria": {
                        "sectors": "Saude",
                        "min_opportunity_score": 70,
                        "min_email_score": 0,
                        "require_email": False,
                        "require_corporate_email": False,
                        "exclude_shared_email": False,
                        "exclude_suppressed": False,
                        "max_leads": 5,
                    },
                },
            )
            before = prioritize_icp_rule(conn, rule["id"])
            update_workspace_company_score_config(conn, {"rules": {"sector_bonus": {"Saude": 30}}})
            rescore_workspace_companies(conn, {"limit": 10})
            after = prioritize_icp_rule(conn, rule["id"])

            self.assertEqual(before["summary"]["suggested"], 0)
            self.assertEqual(before["summary"]["blocked"], 1)
            self.assertEqual(after["summary"]["suggested"], 1)
            self.assertEqual(after["items"][0]["reason"]["company_score"], 76)
            self.assertIn("Score da empresa atingiu minimo: 76", after["items"][0]["reason"]["matched"])


if __name__ == "__main__":
    unittest.main()
