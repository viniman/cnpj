import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    add_companies_to_list,
    create_campaign,
    create_email_template,
    create_leads_from_list,
    create_list,
    create_sequence,
    decide_handoff,
    enroll_sequence_from_list,
    list_agent_actions,
    list_handoffs,
    record_inbound_reply,
    simulate_campaign,
    upsert_company,
)


class ReplyHandoffTest(unittest.TestCase):
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

    def seed_send_and_journey(self, conn):
        company_id = upsert_company(
            conn,
            {
                "cnpj": "11.222.333/0001-81",
                "legal_name": "ALFA SOFTWARE LTDA",
                "trade_name": "Alfa Software",
                "status": "Ativa",
                "email": "comercial@alfa.com.br",
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
        lead_list = create_list(conn, "Lista Respostas", "Teste")
        add_companies_to_list(conn, lead_list["id"], [company_id])
        create_leads_from_list(conn, lead_list["id"], "teste resposta")
        lead = conn.execute("SELECT * FROM leads WHERE company_id = ?", (company_id,)).fetchone()
        campaign = create_campaign(
            conn,
            {
                "name": "Campanha resposta",
                "niche": "Software",
                "subject": "Teste",
                "body": "Mensagem simulada",
                "cta_url": "https://usevagou.com.br/contato",
            },
        )
        simulate_campaign(conn, campaign["id"], list_id=lead_list["id"], limit=1)
        send = conn.execute("SELECT * FROM sends WHERE lead_id = ?", (lead["id"],)).fetchone()
        template = create_email_template(
            conn,
            {
                "name": "Primeiro contato resposta",
                "purpose": "first_contact",
                "subject": "Ideia para {{nome_empresa}}",
                "body": "Mensagem para {{nome_empresa}}.",
            },
        )
        sequence = create_sequence(
            conn,
            {
                "name": "Cadencia resposta",
                "steps": [{"name": "Primeiro contato", "template_id": template["id"]}],
            },
        )
        enroll_sequence_from_list(conn, sequence["id"], lead_list["id"])
        return lead["id"], send["id"]

    def test_opt_out_reply_suppresses_email_and_stops_journey(self):
        conn = connect()
        try:
            lead_id, send_id = self.seed_send_and_journey(conn)
            result = record_inbound_reply(
                conn,
                {"send_id": send_id, "subject": "Re: teste", "body": "Por favor remover meu email da lista."},
            )
            self.assertEqual(result["reply"]["classification"], "opt_out")
            self.assertEqual(result["handoff"]["priority"], "urgent")

            suppression = conn.execute("SELECT reason FROM suppression_list WHERE email = ?", ("comercial@alfa.com.br",)).fetchone()
            self.assertEqual(suppression["reason"], "opt_out_reply")
            lead = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
            self.assertEqual(lead["status"], "opt_out")
            journey = conn.execute("SELECT status FROM lead_journey WHERE lead_id = ?", (lead_id,)).fetchone()
            self.assertEqual(journey["status"], "opt_out")
        finally:
            conn.close()

    def test_interest_reply_creates_high_priority_handoff(self):
        conn = connect()
        try:
            lead_id, send_id = self.seed_send_and_journey(conn)
            result = record_inbound_reply(
                conn,
                {"send_id": send_id, "subject": "Re: teste", "body": "Tenho interesse, podemos conversar esta semana?"},
            )
            self.assertEqual(result["reply"]["classification"], "interest_meeting")
            self.assertEqual(result["handoff"]["priority"], "high")
            lead = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
            self.assertEqual(lead["status"], "responded")
            journey = conn.execute("SELECT status FROM lead_journey WHERE lead_id = ?", (lead_id,)).fetchone()
            self.assertEqual(journey["status"], "responded")
        finally:
            conn.close()

    def test_ambiguous_reply_creates_handoff_and_can_be_resolved(self):
        conn = connect()
        try:
            _lead_id, send_id = self.seed_send_and_journey(conn)
            result = record_inbound_reply(conn, {"send_id": send_id, "body": "Ok, entendi."})
            self.assertEqual(result["reply"]["classification"], "ambiguous")
            self.assertEqual(result["handoff"]["status"], "pending")

            resolved = decide_handoff(conn, result["handoff"]["id"], "resolve", "Revisado manualmente")
            self.assertEqual(resolved["status"], "resolved")
            actions = list_agent_actions(conn)["items"]
            self.assertIn("handoff_resolved", [action["action_type"] for action in actions])
        finally:
            conn.close()

    def test_clear_rejection_disqualifies_without_handoff(self):
        conn = connect()
        try:
            lead_id, send_id = self.seed_send_and_journey(conn)
            result = record_inbound_reply(conn, {"send_id": send_id, "body": "No momento nao tenho interesse."})
            self.assertEqual(result["reply"]["classification"], "not_interested")
            self.assertIsNone(result["handoff"])
            lead = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
            self.assertEqual(lead["status"], "disqualified")
            handoffs = list_handoffs(conn, {"status": "pending"})["items"]
            self.assertEqual(handoffs, [])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
