import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db, now_iso
from radar_cnpj.services import create_workspace, create_workspace_snapshot, workspace_comparison


class WorkspaceComparisonTest(unittest.TestCase):
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

    def test_create_workspace_creates_profile_with_zero_metrics(self):
        conn = connect()
        try:
            workspace = create_workspace(
                conn,
                {
                    "name": "Nine",
                    "vertical": "servicos locais",
                    "default_tone": "direto e acolhedor",
                    "sender_name": "Time Nine",
                },
            )
            self.assertEqual(workspace["name"], "Nine")
            self.assertEqual(workspace["profile"]["display_name"], "Nine")
            self.assertEqual(workspace["profile"]["vertical"], "servicos locais")
            self.assertEqual(workspace["metrics"]["companies"], 0)
            self.assertEqual(workspace["metrics"]["pending_handoffs"], 0)
        finally:
            conn.close()

    def test_comparison_reads_metrics_by_workspace(self):
        conn = connect()
        try:
            workspace = create_workspace(conn, {"name": "Vagou"})
            timestamp = now_iso()
            conn.execute(
                """
                INSERT INTO handoffs (
                    org_id, lead_id, reply_classification_id, status, priority,
                    reason, context_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (workspace["id"], None, None, "pending", "high", "Lead quente", "{}", timestamp),
            )
            conn.execute(
                """
                INSERT INTO notifications (
                    org_id, notification_type, severity, channel, status, title,
                    body, source_type, source_id, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workspace["id"],
                    "hot_lead",
                    "high",
                    "local",
                    "pending",
                    "Lead quente",
                    "Teste",
                    "handoff",
                    "1",
                    "{}",
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO agent_cost_log (
                    org_id, operation, provider, model_name, prompt_tokens,
                    completion_tokens, total_tokens, estimated_cost, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (workspace["id"], "classify_reply", "manual", "gpt-5-mini", 10, 5, 15, 0.001, timestamp),
            )
            data = workspace_comparison(conn)
            by_name = {item["name"]: item for item in data["workspaces"]}
            self.assertEqual(by_name["Vagou"]["metrics"]["pending_handoffs"], 1)
            self.assertEqual(by_name["Vagou"]["metrics"]["pending_notifications"], 1)
            self.assertEqual(by_name["Vagou"]["metrics"]["agent_calls"], 1)
            self.assertEqual(by_name["Vagou"]["metrics"]["agent_cost"], 0.001)
        finally:
            conn.close()

    def test_snapshot_stores_current_metrics(self):
        conn = connect()
        try:
            workspace = create_workspace(conn, {"name": "Real Grana"})
            snapshot = create_workspace_snapshot(conn, workspace["id"])
            self.assertEqual(snapshot["org_id"], workspace["id"])
            self.assertEqual(snapshot["workspace_name"], "Real Grana")
            self.assertIn("companies", snapshot["metrics"])
            comparison = workspace_comparison(conn)
            self.assertEqual(len(comparison["snapshots"]), 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
