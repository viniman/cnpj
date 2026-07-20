import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    add_companies_to_list,
    approve_sequence_step,
    create_email_template,
    create_list,
    create_sequence,
    enroll_sequence_from_list,
    list_agent_actions,
    list_approvals,
    list_journeys,
    prepare_next_journey_step,
    reject_sequence_step,
    upsert_company,
)


class SequenceSupervisionTest(unittest.TestCase):
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

    def seed_list_and_templates(self, conn):
        good_id = upsert_company(
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
        blocked_id = upsert_company(
            conn,
            {
                "cnpj": "22.333.444/0001-81",
                "legal_name": "BETA CONSULTORIA LTDA",
                "trade_name": "Beta Consultoria",
                "status": "Ativa",
                "email": "contato@beta.com.br",
                "main_cnae_code": "7020400",
                "main_cnae_description": "Consultoria",
                "city": "Curitiba",
                "state": "PR",
                "capital_social": 100000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )
        lead_list = create_list(conn, "Lista Sequencia", "Teste")
        add_companies_to_list(conn, lead_list["id"], [good_id, blocked_id])
        first = create_email_template(
            conn,
            {
                "name": "Primeiro contato",
                "purpose": "first_contact",
                "subject": "Ideia para {{nome_empresa}}",
                "body": "Vi que a {{nome_empresa}} {{motivo_contato}}.",
            },
        )
        follow = create_email_template(
            conn,
            {
                "name": "Follow-up",
                "purpose": "follow_up",
                "subject": "Retomando {{nome_empresa}}",
                "body": "Retomando a conversa sobre {{cidade}}.",
            },
        )
        return lead_list["id"], first["id"], follow["id"]

    def test_enroll_sequence_creates_pending_approval_for_eligible_lead(self):
        conn = connect()
        try:
            list_id, first_template_id, _follow_template_id = self.seed_list_and_templates(conn)
            sequence = create_sequence(
                conn,
                {
                    "name": "Cadencia inicial",
                    "steps": [{"name": "Primeiro contato", "template_id": first_template_id}],
                },
            )
            result = enroll_sequence_from_list(conn, sequence["id"], list_id)
            self.assertEqual(result["enrolled"], 1)
            self.assertEqual(result["approvals"], 1)

            approvals = list_approvals(conn)["items"]
            self.assertEqual(len(approvals), 1)
            self.assertEqual(approvals[0]["status"], "pending")
            self.assertIn("Alfa Software", approvals[0]["context"]["subject"])

            journeys = list_journeys(conn)["items"]
            self.assertEqual(len(journeys), 1)
            self.assertEqual(journeys[0]["status"], "pending_approval")
        finally:
            conn.close()

    def test_approve_step_creates_simulated_send_and_next_waiting_step(self):
        conn = connect()
        try:
            list_id, first_template_id, follow_template_id = self.seed_list_and_templates(conn)
            sequence = create_sequence(
                conn,
                {
                    "name": "Cadencia com follow",
                    "steps": [
                        {"name": "Primeiro contato", "template_id": first_template_id},
                        {"name": "Follow-up", "template_id": follow_template_id, "wait_days": 2},
                    ],
                },
            )
            enroll_sequence_from_list(conn, sequence["id"], list_id)
            approval = list_approvals(conn)["items"][0]
            approved = approve_sequence_step(conn, approval["id"], "Aprovado em teste")
            self.assertEqual(approved["approval"]["status"], "approved")
            self.assertEqual(approved["journey"]["status"], "waiting")
            self.assertEqual(approved["journey"]["current_step_number"], 2)

            send = conn.execute("SELECT status, provider FROM sends WHERE id = ?", (approved["send_id"],)).fetchone()
            self.assertEqual(send["status"], "simulated_sent")
            self.assertEqual(send["provider"], "simulated")

            prepared = prepare_next_journey_step(conn, approved["journey"]["id"])
            self.assertEqual(prepared["journey"]["status"], "pending_approval")
            self.assertTrue(prepared["approval_id"])

            actions = list_agent_actions(conn)["items"]
            action_types = [action["action_type"] for action in actions]
            self.assertIn("step_approved_and_simulated", action_types)
            self.assertIn("approval_requested", action_types)
        finally:
            conn.close()

    def test_reject_step_does_not_create_send(self):
        conn = connect()
        try:
            list_id, first_template_id, _follow_template_id = self.seed_list_and_templates(conn)
            sequence = create_sequence(
                conn,
                {
                    "name": "Cadencia rejeitada",
                    "steps": [{"name": "Primeiro contato", "template_id": first_template_id}],
                },
            )
            enroll_sequence_from_list(conn, sequence["id"], list_id)
            approval = list_approvals(conn)["items"][0]
            rejected = reject_sequence_step(conn, approval["id"], "Copy precisa revisao")
            self.assertEqual(rejected["approval"]["status"], "rejected")
            sends = conn.execute("SELECT COUNT(*) AS total FROM sends").fetchone()["total"]
            self.assertEqual(sends, 0)
            journeys = list_journeys(conn)["items"]
            self.assertEqual(journeys[0]["status"], "rejected")
            self.assertEqual(journeys[0]["block_reason"], "Copy precisa revisao")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

