import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    add_companies_to_list,
    command_center,
    command_center_action,
    create_email_template,
    create_leads_from_list,
    create_list,
    create_meeting,
    create_cadence,
    create_workspace,
    enroll_cadence_from_list,
    lead_timeline,
    record_inbound_reply,
    set_current_workspace,
    upsert_company,
)


class CommandCenterTest(unittest.TestCase):
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

    def seed_command_center_context(self, conn):
        company_id = upsert_company(
            conn,
            {
                "cnpj": "33.444.555/0001-66",
                "legal_name": "GAMA OPS LTDA",
                "trade_name": "Gama Ops",
                "status": "Ativa",
                "email": "comercial@gamaops.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Curitiba",
                "state": "PR",
                "capital_social": 300000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )
        lead_list = create_list(conn, "Lista Command Center", "Teste")
        add_companies_to_list(conn, lead_list["id"], [company_id])
        create_leads_from_list(conn, lead_list["id"], "teste command center")
        lead = conn.execute(
            "SELECT * FROM leads WHERE company_id = ? AND list_id = ? ORDER BY id DESC LIMIT 1",
            (company_id, lead_list["id"]),
        ).fetchone()
        template = create_email_template(
            conn,
            {
                "name": "Primeiro contato comando",
                "purpose": "first_contact",
                "subject": "Ideia para {{nome_empresa}}",
                "body": "Mensagem para {{nome_empresa}}.",
            },
        )
        cadence = create_cadence(
            conn,
            {
                "name": "Cadencia comando",
                "steps": [{"name": "Primeiro contato", "template_id": template["id"]}],
            },
        )
        enroll_cadence_from_list(conn, cadence["id"], lead_list["id"])
        record_inbound_reply(
            conn,
            {
                "lead_id": lead["id"],
                "email": lead["email"],
                "subject": "Re: ideia",
                "body": "Tenho interesse, podemos conversar esta semana?",
            },
        )
        create_meeting(
            conn,
            {
                "lead_id": lead["id"],
                "scheduled_at": "2026-07-21T15:00",
                "notes": "Reuniao aberta para Command Center.",
            },
        )
        return lead["id"]

    def seed_pending_approval(self, conn):
        company_id = upsert_company(
            conn,
            {
                "cnpj": "44.555.666/0001-77",
                "legal_name": "DELTA FLOW LTDA",
                "trade_name": "Delta Flow",
                "status": "Ativa",
                "email": "comercial@deltaflow.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software",
                "city": "Sao Paulo",
                "state": "SP",
                "capital_social": 180000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )
        lead_list = create_list(conn, "Lista Approval Command", "Teste")
        add_companies_to_list(conn, lead_list["id"], [company_id])
        create_leads_from_list(conn, lead_list["id"], "teste approval command")
        template = create_email_template(
            conn,
            {
                "name": "Primeiro contato approval",
                "purpose": "first_contact",
                "subject": "Ideia para {{nome_empresa}}",
                "body": "Mensagem para {{nome_empresa}}.",
            },
        )
        cadence = create_cadence(
            conn,
            {
                "name": "Cadencia approval",
                "steps": [{"name": "Primeiro contato", "template_id": template["id"]}],
            },
        )
        enroll_cadence_from_list(conn, cadence["id"], lead_list["id"])
        approval = conn.execute("SELECT * FROM approval_queue WHERE status = 'pending' ORDER BY id DESC LIMIT 1").fetchone()
        lead = conn.execute(
            "SELECT * FROM leads WHERE company_id = ? AND list_id = ? ORDER BY id DESC LIMIT 1",
            (company_id, lead_list["id"]),
        ).fetchone()
        return approval["id"], lead["id"]

    def test_command_center_aggregates_inbox_kanban_and_activity(self):
        conn = connect()
        try:
            lead_id = self.seed_command_center_context(conn)
            data = command_center(conn)
            self.assertGreaterEqual(data["metrics"]["pending_approvals"], 1)
            self.assertGreaterEqual(data["metrics"]["pending_handoffs"], 1)
            self.assertGreaterEqual(data["metrics"]["open_meetings"], 1)

            source_types = {item["source_type"] for item in data["inbox"]["items"]}
            self.assertTrue({"approval", "handoff", "meeting"}.issubset(source_types))
            self.assertTrue(all(item.get("source_id") for item in data["inbox"]["items"]))
            self.assertTrue(all(item.get("origin_label") for item in data["inbox"]["items"]))

            cards = [card for column in data["kanban"]["columns"] for card in column["items"]]
            self.assertIn(lead_id, [card["lead_id"] for card in cards])
            meeting_column = next(column for column in data["kanban"]["columns"] if column["key"] == "meeting")
            self.assertIn(lead_id, [card["lead_id"] for card in meeting_column["items"]])

            actions = [item["action_type"] for item in data["activity"]["items"]]
            self.assertIn("approval_requested", actions)
            self.assertIn("reply_classified", actions)
            self.assertIn("meeting_created", actions)
        finally:
            conn.close()

    def test_command_center_action_approves_approval(self):
        conn = connect()
        try:
            approval_id, lead_id = self.seed_pending_approval(conn)
            result = command_center_action(
                conn,
                {
                    "source_type": "approval",
                    "source_id": approval_id,
                    "decision": "approve",
                    "note": "Aprovado pela inbox unificada",
                },
            )
            self.assertEqual(result["source_type"], "approval")
            self.assertEqual(result["decision"], "approve")
            approval = conn.execute("SELECT status FROM approval_queue WHERE id = ?", (approval_id,)).fetchone()
            self.assertEqual(approval["status"], "approved")
            send = conn.execute("SELECT id FROM sends WHERE lead_id = ?", (lead_id,)).fetchone()
            self.assertIsNotNone(send)
            inbox_ids = [
                item["source_id"]
                for item in result["command_center"]["inbox"]["items"]
                if item["source_type"] == "approval"
            ]
            self.assertNotIn(approval_id, inbox_ids)
        finally:
            conn.close()

    def test_command_center_action_decides_handoff_and_meeting(self):
        conn = connect()
        try:
            lead_id = self.seed_command_center_context(conn)
            handoff = conn.execute("SELECT * FROM handoffs WHERE lead_id = ? AND status = 'pending'", (lead_id,)).fetchone()
            meeting = conn.execute("SELECT * FROM meetings WHERE lead_id = ? AND status = 'scheduled'", (lead_id,)).fetchone()

            handoff_result = command_center_action(
                conn,
                {
                    "source_type": "handoff",
                    "source_id": handoff["id"],
                    "decision": "resolve",
                    "note": "Resolvido pela inbox unificada",
                },
            )
            self.assertEqual(handoff_result["result"]["status"], "resolved")

            meeting_result = command_center_action(
                conn,
                {
                    "source_type": "meeting",
                    "source_id": meeting["id"],
                    "decision": "complete",
                    "note": "Reuniao concluida pela inbox unificada",
                },
            )
            self.assertEqual(meeting_result["result"]["status"], "completed")
            lead = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
            self.assertEqual(lead["status"], "qualified")
        finally:
            conn.close()

    def test_command_center_action_rejects_invalid_decision(self):
        conn = connect()
        try:
            approval_id, _lead_id = self.seed_pending_approval(conn)
            with self.assertRaises(ValueError):
                command_center_action(
                    conn,
                    {
                        "source_type": "approval",
                        "source_id": approval_id,
                        "decision": "complete",
                    },
                )
        finally:
            conn.close()

    def test_lead_timeline_reconstructs_operational_journey(self):
        conn = connect()
        try:
            approval_id, lead_id = self.seed_pending_approval(conn)
            command_center_action(
                conn,
                {
                    "source_type": "approval",
                    "source_id": approval_id,
                    "decision": "approve",
                    "note": "Aprovado para timeline",
                },
            )
            reply = record_inbound_reply(
                conn,
                {
                    "lead_id": lead_id,
                    "subject": "Re: ideia",
                    "body": "Tenho interesse, podemos conversar esta semana?",
                },
            )
            command_center_action(
                conn,
                {
                    "source_type": "handoff",
                    "source_id": reply["handoff"]["id"],
                    "decision": "resolve",
                    "note": "Resolvido para timeline",
                },
            )
            meeting = create_meeting(
                conn,
                {
                    "lead_id": lead_id,
                    "scheduled_at": "2026-07-21T15:00",
                    "notes": "Reuniao para timeline.",
                },
            )
            command_center_action(
                conn,
                {
                    "source_type": "meeting",
                    "source_id": meeting["id"],
                    "decision": "complete",
                    "note": "Concluida para timeline",
                },
            )

            timeline = lead_timeline(conn, lead_id)
            self.assertEqual(timeline["lead"]["id"], lead_id)
            self.assertEqual(timeline["company"]["trade_name"], "Delta Flow")
            kinds = {item["kind"] for item in timeline["timeline"]}
            self.assertTrue(
                {
                    "approval",
                    "approval_decision",
                    "send",
                    "event",
                    "reply",
                    "handoff",
                    "handoff_decision",
                    "meeting",
                    "meeting_status",
                    "conversion",
                    "agent_action",
                }.issubset(kinds)
            )
            self.assertGreaterEqual(timeline["summary"]["timeline_items"], 10)
            self.assertEqual(timeline["summary"]["approvals"], 2)
            self.assertGreaterEqual(timeline["summary"]["actions"], 5)
            occurred_at = [item["occurred_at"] for item in timeline["timeline"]]
            self.assertEqual(occurred_at, sorted(occurred_at))
            self.assertTrue(all(item.get("source_table") for item in timeline["timeline"]))
            self.assertTrue(all(item.get("origin_label") for item in timeline["timeline"]))
        finally:
            conn.close()

    def test_lead_timeline_returns_none_for_missing_lead(self):
        conn = connect()
        try:
            self.assertIsNone(lead_timeline(conn, 9999))
        finally:
            conn.close()

    def test_command_center_and_replay_follow_active_workspace(self):
        conn = connect()
        try:
            internal_approval_id, internal_lead_id = self.seed_pending_approval(conn)
            internal_snapshot = command_center(conn)
            self.assertGreaterEqual(internal_snapshot["metrics"]["pending_approvals"], 1)
            self.assertIsNotNone(lead_timeline(conn, internal_lead_id))

            workspace = create_workspace(conn, {"name": "Nine Command Center"})
            set_current_workspace(conn, workspace["id"])

            empty_snapshot = command_center(conn)
            self.assertEqual(empty_snapshot["metrics"]["pending_approvals"], 0)
            self.assertEqual(empty_snapshot["metrics"]["pending_handoffs"], 0)
            self.assertEqual(empty_snapshot["metrics"]["open_meetings"], 0)
            self.assertEqual(empty_snapshot["inbox"]["items"], [])
            empty_cards = [card for column in empty_snapshot["kanban"]["columns"] for card in column["items"]]
            self.assertEqual(empty_cards, [])
            self.assertEqual(empty_snapshot["activity"]["items"], [])
            self.assertIsNone(lead_timeline(conn, internal_lead_id))
            with self.assertRaises(ValueError):
                command_center_action(
                    conn,
                    {
                        "source_type": "approval",
                        "source_id": internal_approval_id,
                        "decision": "approve",
                    },
                )

            scoped_lead_id = self.seed_command_center_context(conn)
            scoped_snapshot = command_center(conn)
            self.assertGreaterEqual(scoped_snapshot["metrics"]["pending_approvals"], 1)
            self.assertGreaterEqual(scoped_snapshot["metrics"]["pending_handoffs"], 1)
            self.assertGreaterEqual(scoped_snapshot["metrics"]["open_meetings"], 1)
            scoped_cards = [card for column in scoped_snapshot["kanban"]["columns"] for card in column["items"]]
            self.assertEqual({card["lead_id"] for card in scoped_cards}, {scoped_lead_id})
            self.assertIsNotNone(lead_timeline(conn, scoped_lead_id))

            set_current_workspace(conn, 1)
            restored_snapshot = command_center(conn)
            restored_cards = [card for column in restored_snapshot["kanban"]["columns"] for card in column["items"]]
            self.assertIn(internal_lead_id, {card["lead_id"] for card in restored_cards})
            self.assertIsNone(lead_timeline(conn, scoped_lead_id))
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
