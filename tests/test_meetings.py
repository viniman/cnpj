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
    create_meeting_from_handoff,
    create_sequence,
    enroll_sequence_from_list,
    list_agent_actions,
    list_meetings,
    record_inbound_reply,
    simulate_campaign,
    update_meeting_status,
    upsert_company,
)


class MeetingSchedulingTest(unittest.TestCase):
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

    def seed_reply(self, conn, body):
        company_id = upsert_company(
            conn,
            {
                "cnpj": "22.333.444/0001-55",
                "legal_name": "BETA CLOUD LTDA",
                "trade_name": "Beta Cloud",
                "status": "Ativa",
                "email": "comercial@betacloud.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Sao Paulo",
                "state": "SP",
                "capital_social": 250000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )
        lead_list = create_list(conn, "Lista Reunioes", "Teste")
        add_companies_to_list(conn, lead_list["id"], [company_id])
        create_leads_from_list(conn, lead_list["id"], "teste reuniao")
        lead = conn.execute("SELECT * FROM leads WHERE company_id = ?", (company_id,)).fetchone()
        campaign = create_campaign(
            conn,
            {
                "name": "Campanha reuniao",
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
                "name": "Primeiro contato reuniao",
                "purpose": "first_contact",
                "subject": "Ideia para {{nome_empresa}}",
                "body": "Mensagem para {{nome_empresa}}.",
            },
        )
        sequence = create_sequence(
            conn,
            {
                "name": "Cadencia reuniao",
                "steps": [{"name": "Primeiro contato", "template_id": template["id"]}],
            },
        )
        enroll_sequence_from_list(conn, sequence["id"], lead_list["id"])
        reply = record_inbound_reply(conn, {"send_id": send["id"], "subject": "Re: teste", "body": body})
        return lead["id"], reply

    def test_create_meeting_from_handoff_resolves_handoff_and_updates_lead(self):
        conn = connect()
        try:
            lead_id, reply = self.seed_reply(conn, "Tenho interesse, podemos conversar esta semana?")
            meeting = create_meeting_from_handoff(
                conn,
                reply["handoff"]["id"],
                {
                    "scheduled_at": "2026-07-21T14:00:00-03:00",
                    "meeting_url": "https://meet.example.com/beta",
                    "notes": "Horario combinado por resposta.",
                },
            )
            self.assertEqual(meeting["status"], "scheduled")
            self.assertEqual(meeting["lead_id"], lead_id)
            self.assertEqual(meeting["handoff_id"], reply["handoff"]["id"])

            handoff = conn.execute("SELECT status FROM handoffs WHERE id = ?", (reply["handoff"]["id"],)).fetchone()
            self.assertEqual(handoff["status"], "resolved")
            lead = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
            self.assertEqual(lead["status"], "meeting_scheduled")
            conversion = conn.execute("SELECT conversion_type FROM conversions WHERE lead_id = ? ORDER BY id DESC LIMIT 1", (lead_id,)).fetchone()
            self.assertEqual(conversion["conversion_type"], "meeting_scheduled")
            actions = [action["action_type"] for action in list_agent_actions(conn)["items"]]
            self.assertIn("meeting_created", actions)
        finally:
            conn.close()

    def test_meeting_is_blocked_for_opt_out_reply(self):
        conn = connect()
        try:
            _lead_id, reply = self.seed_reply(conn, "Por favor remover meu email da lista.")
            with self.assertRaises(ValueError):
                create_meeting_from_handoff(conn, reply["handoff"]["id"], {"scheduled_at": "2026-07-21T14:00:00-03:00"})
            meetings = list_meetings(conn)["items"]
            self.assertEqual(meetings, [])
        finally:
            conn.close()

    def test_update_meeting_status_completed_marks_lead_qualified(self):
        conn = connect()
        try:
            lead_id, reply = self.seed_reply(conn, "Tenho interesse, podemos conversar esta semana?")
            meeting = create_meeting_from_handoff(conn, reply["handoff"]["id"], {"scheduled_at": "2026-07-21T14:00:00-03:00"})
            updated = update_meeting_status(conn, meeting["id"], "completed", "Reuniao feita; lead qualificado.")
            self.assertEqual(updated["status"], "completed")
            lead = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
            self.assertEqual(lead["status"], "qualified")
            conversion_types = [
                row["conversion_type"]
                for row in conn.execute("SELECT conversion_type FROM conversions WHERE lead_id = ? ORDER BY id", (lead_id,)).fetchall()
            ]
            self.assertIn("meeting_completed", conversion_types)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
