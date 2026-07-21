import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    create_icp_from_saved_filter,
    create_saved_filter,
    create_workspace,
    list_icp_rules,
    list_saved_filters,
    search_companies,
    set_current_workspace,
    upsert_company,
)


class SavedSegmentTest(unittest.TestCase):
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

    def seed_company(self, conn, name, state="SP", city="Sao Paulo", cnae="6201501", email="contato@empresa.com.br"):
        return upsert_company(
            conn,
            {
                "cnpj": "12.345.678/%04d-95" % (abs(hash(name)) % 10000),
                "legal_name": name,
                "trade_name": name.split()[0],
                "status": "Ativa",
                "email": email,
                "main_cnae_code": cnae,
                "main_cnae_description": "Software sob encomenda",
                "city": city,
                "state": state,
                "size": "ME",
                "capital_social": 150000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )

    def test_create_saved_filter_normalizes_filters_and_records_snapshot(self):
        conn = connect()
        try:
            self.seed_company(conn, "ALVO SEGMENTO LTDA")
            self.seed_company(conn, "OUTRO SEGMENTO LTDA", state="RJ", city="Rio de Janeiro")

            saved = create_saved_filter(
                conn,
                {
                    "name": "Software SP com email",
                    "filters": {"state": "sp", "cnae": "620", "has_email": True, "limit": 80, "offset": 20},
                },
            )

            self.assertEqual(saved["filters"], {"state": "SP", "cnae": "620", "has_email": "1"})
            self.assertEqual(saved["snapshot"]["total"], 1)
            self.assertIsNotNone(saved["snapshot"]["captured_at"])
            self.assertEqual(list_saved_filters(conn)["items"][0]["id"], saved["id"])
        finally:
            conn.close()

    def test_saved_filter_can_be_applied_to_company_search(self):
        conn = connect()
        try:
            self.seed_company(conn, "APLICA SEGMENTO LTDA", state="MG", city="Belo Horizonte")
            self.seed_company(conn, "FORA SEGMENTO LTDA", state="SP", city="Sao Paulo")
            saved = create_saved_filter(conn, {"name": "Minas", "filters": {"state": "MG"}})

            result = search_companies(conn, saved["filters"])

            self.assertEqual(result["total"], 1)
            self.assertEqual(result["items"][0]["legal_name"], "APLICA SEGMENTO LTDA")
        finally:
            conn.close()

    def test_saved_filter_converts_to_icp_rule_with_source_filters(self):
        conn = connect()
        try:
            saved = create_saved_filter(
                conn,
                {
                    "name": "ICP software SP",
                    "filters": {"state": "SP", "city": "Sao Paulo", "cnae": "620", "has_email": "1", "min_score": "20"},
                },
            )

            result = create_icp_from_saved_filter(conn, saved["id"], {"name": "ICP convertido", "max_leads": 25})
            rule = result["icp_rule"]

            self.assertEqual(rule["name"], "ICP convertido")
            self.assertEqual(rule["criteria"]["states"], ["SP"])
            self.assertEqual(rule["criteria"]["cities"], ["sao paulo"])
            self.assertEqual(rule["criteria"]["cnaes"], ["620"])
            self.assertEqual(rule["criteria"]["min_opportunity_score"], 20)
            self.assertTrue(rule["criteria"]["require_email"])
            self.assertEqual(rule["criteria"]["max_leads"], 25)
            self.assertEqual(rule["criteria"]["source_filter_id"], saved["id"])
            self.assertEqual(rule["criteria"]["source_filters"]["state"], "SP")
        finally:
            conn.close()

    def test_saved_filters_are_scoped_to_active_workspace(self):
        conn = connect()
        try:
            internal = create_saved_filter(conn, {"name": "Interno SP", "filters": {"state": "SP"}})
            workspace = create_workspace(conn, {"name": "Nine Segments"})
            set_current_workspace(conn, workspace["id"])

            self.assertEqual(list_saved_filters(conn)["items"], [])
            scoped = create_saved_filter(conn, {"name": "Nine RJ", "filters": {"state": "RJ"}})
            self.assertEqual([item["id"] for item in list_saved_filters(conn)["items"]], [scoped["id"]])
            self.assertIsNone(next((item for item in list_icp_rules(conn)["items"] if item["name"] == "Interno SP"), None))

            set_current_workspace(conn, 1)
            self.assertEqual([item["id"] for item in list_saved_filters(conn)["items"]], [internal["id"]])
            with self.assertRaises(ValueError):
                create_icp_from_saved_filter(conn, scoped["id"], {})
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
