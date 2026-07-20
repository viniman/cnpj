import os
import tempfile
import unittest
from datetime import datetime, timedelta

from radar_cnpj.database import connect, init_db, now_iso
from radar_cnpj.services import (
    create_okr,
    generate_notifications,
    list_notifications,
    update_notification_status,
)


class NotificationCenterTest(unittest.TestCase):
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

    def insert_handoff(self, conn, priority="high", reason="Lead demonstrou interesse em reuniao"):
        timestamp = now_iso()
        cursor = conn.execute(
            """
            INSERT INTO handoffs (
                org_id, lead_id, reply_classification_id, status, priority,
                reason, context_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (1, None, None, "pending", priority, reason, "{}", timestamp),
        )
        return cursor.lastrowid

    def insert_pause_event(self, conn):
        cursor = conn.execute(
            """
            INSERT INTO pause_events (campaign_id, pause_type, reason, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (None, "auto", "Bounce acima do limite preventivo", now_iso()),
        )
        return cursor.lastrowid

    def test_generate_hot_lead_notification_is_idempotent(self):
        conn = connect()
        try:
            handoff_id = self.insert_handoff(conn)
            first = generate_notifications(conn)
            self.assertEqual(first["created"], 1)
            self.assertEqual(first["items"][0]["notification_type"], "hot_lead")
            self.assertEqual(first["items"][0]["source_id"], str(handoff_id))

            second = generate_notifications(conn)
            self.assertEqual(second["created"], 0)
            listed = list_notifications(conn)
            self.assertEqual(listed["summary"]["pending"], 1)
        finally:
            conn.close()

    def test_generate_pause_and_okr_notifications(self):
        conn = connect()
        try:
            self.insert_handoff(conn)
            self.insert_pause_event(conn)
            period_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
            create_okr(
                conn,
                {
                    "title": "Validar alertas",
                    "period_end": period_end,
                    "key_results": [
                        {"title": "Resolver 1 handoff", "kpi_key": "pending_handoffs", "target_value": 1},
                        {"title": "Gerar 10 respostas", "kpi_key": "replies_received", "target_value": 10},
                    ],
                },
            )
            result = generate_notifications(conn)
            types = {item["notification_type"] for item in result["items"]}
            self.assertIn("campaign_paused", types)
            self.assertIn("okr_achieved", types)
            self.assertIn("okr_at_risk", types)
            self.assertIn("hot_lead", types)
        finally:
            conn.close()

    def test_notification_status_actions_do_not_change_source(self):
        conn = connect()
        try:
            handoff_id = self.insert_handoff(conn)
            notification = generate_notifications(conn)["items"][0]

            read = update_notification_status(conn, notification["id"], "read")
            self.assertEqual(read["status"], "read")
            handoff = conn.execute("SELECT status FROM handoffs WHERE id = ?", (handoff_id,)).fetchone()
            self.assertEqual(handoff["status"], "pending")

            dismissed = update_notification_status(conn, notification["id"], "dismissed")
            self.assertEqual(dismissed["status"], "dismissed")
            summary = list_notifications(conn)["summary"]
            self.assertEqual(summary["dismissed"], 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
