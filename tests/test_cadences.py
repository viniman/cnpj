import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    add_companies_to_list,
    approve_cadence_step,
    create_email_template,
    create_list,
    create_cadence,
    create_workspace,
    enroll_cadence_from_list,
    get_cadence,
    list_agent_actions,
    list_approvals,
    list_journeys,
    list_cadences,
    prepare_next_journey_step,
    reject_cadence_step,
    set_current_workspace,
    upsert_company,
)


class CadenceSupervisionTest(unittest.TestCase):
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
        lead_list = create_list(conn, "Lista Cadencia", "Teste")
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

    def test_enroll_cadence_creates_pending_approval_for_eligible_lead(self):
        conn = connect()
        try:
            list_id, first_template_id, _follow_template_id = self.seed_list_and_templates(conn)
            cadence = create_cadence(
                conn,
                {
                    "name": "Cadencia inicial",
                    "steps": [{"name": "Primeiro contato", "template_id": first_template_id}],
                },
            )
            result = enroll_cadence_from_list(conn, cadence["id"], list_id)
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
            cadence = create_cadence(
                conn,
                {
                    "name": "Cadencia com follow",
                    "steps": [
                        {"name": "Primeiro contato", "template_id": first_template_id},
                        {"name": "Follow-up", "template_id": follow_template_id, "wait_days": 2},
                    ],
                },
            )
            enroll_cadence_from_list(conn, cadence["id"], list_id)
            approval = list_approvals(conn)["items"][0]
            approved = approve_cadence_step(conn, approval["id"], "Aprovado em teste")
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
            cadence = create_cadence(
                conn,
                {
                    "name": "Cadencia rejeitada",
                    "steps": [{"name": "Primeiro contato", "template_id": first_template_id}],
                },
            )
            enroll_cadence_from_list(conn, cadence["id"], list_id)
            approval = list_approvals(conn)["items"][0]
            rejected = reject_cadence_step(conn, approval["id"], "Copy precisa revisao")
            self.assertEqual(rejected["approval"]["status"], "rejected")
            sends = conn.execute("SELECT COUNT(*) AS total FROM sends").fetchone()["total"]
            self.assertEqual(sends, 0)
            journeys = list_journeys(conn)["items"]
            self.assertEqual(journeys[0]["status"], "rejected")
            self.assertEqual(journeys[0]["block_reason"], "Copy precisa revisao")
        finally:
            conn.close()

    def test_cadences_follow_active_workspace(self):
        conn = connect()
        try:
            internal_list_id, internal_template_id, _follow_template_id = self.seed_list_and_templates(conn)
            internal_cadence = create_cadence(
                conn,
                {
                    "name": "Cadencia interna",
                    "steps": [{"name": "Primeiro contato", "template_id": internal_template_id}],
                },
            )
            enroll_cadence_from_list(conn, internal_cadence["id"], internal_list_id)
            internal_approval = list_approvals(conn)["items"][0]
            internal_journey = list_journeys(conn)["items"][0]

            workspace = create_workspace(conn, {"name": "Nine Cadencias"})
            set_current_workspace(conn, workspace["id"])

            self.assertEqual(list_cadences(conn)["items"], [])
            self.assertEqual(list_approvals(conn)["items"], [])
            self.assertEqual(list_journeys(conn)["items"], [])
            self.assertEqual(list_agent_actions(conn)["items"], [])
            self.assertIsNone(get_cadence(conn, internal_cadence["id"]))
            with self.assertRaises(ValueError):
                enroll_cadence_from_list(conn, internal_cadence["id"], internal_list_id)
            with self.assertRaises(ValueError):
                approve_cadence_step(conn, internal_approval["id"], "Nao deveria aprovar")
            with self.assertRaises(ValueError):
                prepare_next_journey_step(conn, internal_journey["id"])

            scoped_list_id, scoped_template_id, _scoped_follow_id = self.seed_list_and_templates(conn)
            scoped_cadence = create_cadence(
                conn,
                {
                    "name": "Cadencia Nine",
                    "steps": [{"name": "Primeiro contato", "template_id": scoped_template_id}],
                },
            )
            self.assertEqual(scoped_cadence["org_id"], workspace["id"])
            result = enroll_cadence_from_list(conn, scoped_cadence["id"], scoped_list_id)
            self.assertEqual(result["enrolled"], 1)
            scoped_approval = list_approvals(conn)["items"][0]
            self.assertEqual(scoped_approval["org_id"], workspace["id"])

            action_orgs = {
                row["org_id"]
                for row in conn.execute("SELECT org_id FROM agent_actions WHERE cadence_id = ?", (scoped_cadence["id"],)).fetchall()
            }
            self.assertEqual(action_orgs, {workspace["id"]})

            set_current_workspace(conn, 1)
            self.assertEqual([item["id"] for item in list_cadences(conn)["items"]], [internal_cadence["id"]])
            self.assertEqual([item["id"] for item in list_approvals(conn)["items"]], [internal_approval["id"]])
            with self.assertRaises(ValueError):
                reject_cadence_step(conn, scoped_approval["id"], "Nao deveria rejeitar")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

