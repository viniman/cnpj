import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    add_companies_to_list,
    add_suppression,
    create_campaign,
    create_leads_from_list,
    create_list,
    create_workspace,
    get_campaign,
    list_campaigns,
    list_experiment_leads,
    record_campaign_event,
    set_current_workspace,
    simulate_campaign,
    upsert_company,
)


class EmailExperimentTest(unittest.TestCase):
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

    def seed_list(self, conn):
        companies = [
            ("11.222.333/0001-81", "ALFA LTDA", "comercial@alfa.com.br"),
            ("22.333.444/0001-81", "BETA LTDA", "contato@beta.com.br"),
            ("33.444.555/0001-81", "GAMA LTDA", "comercial@gama.com.br"),
        ]
        ids = []
        for cnpj, name, email in companies:
            ids.append(
                upsert_company(
                    conn,
                    {
                        "cnpj": cnpj,
                        "legal_name": name,
                        "status": "Ativa",
                        "email": email,
                        "main_cnae_code": "6201501",
                        "main_cnae_description": "Software",
                        "city": "Sao Paulo",
                        "state": "SP",
                        "capital_social": 200000,
                    },
                    "Teste",
                    "fixture",
                    "Teste automatizado",
                )
            )
        lead_list = create_list(conn, "Lista Experimento", "Teste")
        add_companies_to_list(conn, lead_list["id"], ids)
        return lead_list["id"]

    def test_create_leads_from_list_applies_guardrails(self):
        conn = connect()
        try:
            list_id = self.seed_list(conn)
            add_suppression(conn, "comercial@gama.com.br", "nao contactar")
            result = create_leads_from_list(conn, list_id)
            self.assertEqual(result["total"], 3)
            self.assertEqual(result["eligible"], 1)
            self.assertEqual(result["blocked"], 2)

            leads = list_experiment_leads(conn)["items"]
            statuses = dict((lead["email"], lead["status"]) for lead in leads)
            self.assertEqual(statuses["comercial@alfa.com.br"], "eligible")
            self.assertEqual(statuses["contato@beta.com.br"], "blocked")
            self.assertEqual(statuses["comercial@gama.com.br"], "blocked")
        finally:
            conn.close()

    def test_simulated_campaign_never_uses_real_provider(self):
        conn = connect()
        try:
            list_id = self.seed_list(conn)
            add_suppression(conn, "comercial@gama.com.br", "nao contactar")
            create_leads_from_list(conn, list_id)
            campaign = create_campaign(
                conn,
                {
                    "name": "Teste comercial SP",
                    "niche": "Software SP",
                    "subject": "Ideia rapida",
                    "body": "Podemos conversar sobre uma ideia objetiva?",
                    "cta_url": "https://usevagou.com.br/contato",
                },
            )
            self.assertEqual(campaign["mode"], "simulated")
            result = simulate_campaign(conn, campaign["id"], list_id=list_id, limit=10)
            self.assertEqual(result["simulation"]["sent"], 1)
            self.assertEqual(result["simulation"]["blocked"], 2)
            self.assertEqual(result["funnel"]["sent"], 1)
            self.assertEqual(result["funnel"]["blocked"], 2)

            providers = {
                row["provider"]
                for row in conn.execute("SELECT provider FROM sends WHERE campaign_id = ?", (campaign["id"],)).fetchall()
            }
            self.assertEqual(providers, {"simulated"})
        finally:
            conn.close()

    def test_bounce_event_adds_suppression(self):
        conn = connect()
        try:
            list_id = self.seed_list(conn)
            create_leads_from_list(conn, list_id)
            campaign = create_campaign(
                conn,
                {
                    "name": "Teste bounce",
                    "niche": "Software",
                    "subject": "Teste",
                    "body": "Mensagem simulada",
                    "cta_url": "https://usevagou.com.br/contato",
                },
            )
            simulate_campaign(conn, campaign["id"], list_id=list_id, limit=1)
            send = conn.execute(
                "SELECT id, email FROM sends WHERE campaign_id = ? AND status = 'simulated_sent'",
                (campaign["id"],),
            ).fetchone()
            result = record_campaign_event(conn, {"send_id": send["id"], "event_type": "bounce"})
            self.assertEqual(result["funnel"]["bounce"], 1)
            suppression = conn.execute(
                "SELECT reason FROM suppression_list WHERE email = ?",
                (send["email"],),
            ).fetchone()
            self.assertEqual(suppression["reason"], "bounce")
        finally:
            conn.close()

    def test_experiment_records_follow_active_workspace(self):
        conn = connect()
        try:
            internal_list_id = self.seed_list(conn)
            create_leads_from_list(conn, internal_list_id)
            internal_campaign = create_campaign(
                conn,
                {
                    "name": "Campanha interna",
                    "niche": "Software",
                    "subject": "Teste interno",
                    "body": "Mensagem interna",
                    "cta_url": "https://usevagou.com.br/contato",
                },
            )

            workspace = create_workspace(conn, {"name": "Nine Experimentos"})
            set_current_workspace(conn, workspace["id"])

            self.assertEqual(list_experiment_leads(conn)["items"], [])
            self.assertEqual(list_campaigns(conn)["items"], [])
            self.assertIsNone(get_campaign(conn, internal_campaign["id"]))
            with self.assertRaises(ValueError):
                simulate_campaign(conn, internal_campaign["id"], list_id=internal_list_id, limit=1)

            scoped_list_id = self.seed_list(conn)
            create_leads_from_list(conn, scoped_list_id)
            lead_orgs = {
                row["org_id"]
                for row in conn.execute("SELECT org_id FROM leads WHERE list_id = ?", (scoped_list_id,)).fetchall()
            }
            self.assertEqual(lead_orgs, {workspace["id"]})

            scoped_campaign = create_campaign(
                conn,
                {
                    "name": "Campanha Nine",
                    "niche": "Software",
                    "subject": "Teste Nine",
                    "body": "Mensagem Nine",
                    "cta_url": "https://usevagou.com.br/contato",
                },
            )
            result = simulate_campaign(conn, scoped_campaign["id"], list_id=scoped_list_id, limit=1)
            self.assertEqual(result["simulation"]["attempted"], 1)
            send = conn.execute(
                "SELECT id FROM sends WHERE campaign_id = ? ORDER BY id DESC LIMIT 1",
                (scoped_campaign["id"],),
            ).fetchone()

            set_current_workspace(conn, 1)
            with self.assertRaises(ValueError):
                record_campaign_event(conn, {"send_id": send["id"], "event_type": "replied"})

            set_current_workspace(conn, workspace["id"])
            event_result = record_campaign_event(conn, {"send_id": send["id"], "event_type": "replied"})
            self.assertEqual(event_result["funnel"]["replied"], 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

