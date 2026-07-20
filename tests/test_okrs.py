import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    add_companies_to_list,
    create_list,
    create_leads_from_list,
    create_meeting,
    create_okr,
    okr_dashboard,
    record_inbound_reply,
    update_meeting_status,
    upsert_company,
)


class OkrKpiTest(unittest.TestCase):
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

    def seed_completed_meeting(self, conn):
        company_id = upsert_company(
            conn,
            {
                "cnpj": "55.666.777/0001-88",
                "legal_name": "OMEGA KPI LTDA",
                "trade_name": "Omega KPI",
                "status": "Ativa",
                "email": "comercial@omegakpi.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Belo Horizonte",
                "state": "MG",
                "capital_social": 220000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )
        lead_list = create_list(conn, "Lista OKR", "Teste")
        add_companies_to_list(conn, lead_list["id"], [company_id])
        create_leads_from_list(conn, lead_list["id"], "teste okr")
        lead = conn.execute("SELECT * FROM leads WHERE company_id = ?", (company_id,)).fetchone()
        record_inbound_reply(
            conn,
            {
                "lead_id": lead["id"],
                "email": lead["email"],
                "subject": "Re: ideia",
                "body": "Tenho interesse, podemos conversar esta semana?",
            },
        )
        meeting = create_meeting(
            conn,
            {
                "lead_id": lead["id"],
                "scheduled_at": "2026-07-22T10:00",
                "notes": "Reuniao para KPI.",
            },
        )
        update_meeting_status(conn, meeting["id"], "completed", "Reuniao concluida para KPI.")
        return lead["id"]

    def test_okr_dashboard_returns_default_and_real_kpis(self):
        conn = connect()
        try:
            self.seed_completed_meeting(conn)
            dashboard = okr_dashboard(conn)
            kpis = {item["kpi_key"]: item for item in dashboard["kpis"]}
            self.assertEqual(kpis["active_leads"]["current_value"], 1)
            self.assertEqual(kpis["replies_received"]["current_value"], 1)
            self.assertEqual(kpis["meetings_completed"]["current_value"], 1)
            self.assertEqual(kpis["conversions_registered"]["current_value"], 2)
            self.assertTrue(kpis["meetings_completed"]["formula"])
            self.assertIn("meetings", kpis["meetings_completed"]["source_tables"])
            self.assertEqual(dashboard["objectives"][0]["id"], "default")
            self.assertGreater(dashboard["objectives"][0]["key_results"][1]["progress"], 0)
        finally:
            conn.close()

    def test_create_okr_links_key_result_to_kpi(self):
        conn = connect()
        try:
            self.seed_completed_meeting(conn)
            objective = create_okr(
                conn,
                {
                    "title": "Validar reunioes KPI",
                    "key_results": [
                        {
                            "title": "Concluir 1 reuniao",
                            "kpi_key": "meetings_completed",
                            "target_value": 1,
                        }
                    ],
                },
            )
            self.assertEqual(objective["title"], "Validar reunioes KPI")
            self.assertEqual(objective["key_results"][0]["current_value"], 1)
            self.assertEqual(objective["key_results"][0]["progress"], 100)
        finally:
            conn.close()

    def test_create_okr_rejects_unknown_kpi(self):
        conn = connect()
        try:
            with self.assertRaises(ValueError):
                create_okr(
                    conn,
                    {
                        "title": "OKR invalido",
                        "key_results": [{"title": "Meta", "kpi_key": "nao_existe", "target_value": 1}],
                    },
                )
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
