import os
import tempfile
import unittest
from datetime import datetime, timedelta

from radar_cnpj.database import connect, init_db, now_iso
from radar_cnpj.services import (
    add_companies_to_list,
    audit_events,
    create_list,
    create_okr,
    create_workspace,
    dashboard,
    generate_notifications,
    list_lists,
    list_notifications,
    okr_dashboard,
    set_current_workspace,
    upsert_company,
    workspace_context,
)


class WorkspaceContextTest(unittest.TestCase):
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

    def test_default_context_uses_internal_workspace(self):
        conn = connect()
        try:
            context = workspace_context(conn)
            self.assertEqual(context["active_workspace"]["id"], 1)
            self.assertEqual(context["active_workspace"]["name"], "Workspace interno")
            self.assertGreaterEqual(len(context["workspaces"]), 1)
        finally:
            conn.close()

    def test_switching_workspace_scopes_lists_and_dashboard(self):
        conn = connect()
        try:
            internal_list = create_list(conn, "Lista interna", "Escopo inicial")
            workspace = create_workspace(conn, {"name": "Nine"})

            switched = set_current_workspace(conn, workspace["id"])
            self.assertEqual(switched["active_workspace"]["id"], workspace["id"])
            self.assertEqual(list_lists(conn), [])

            company_id = upsert_company(
                conn,
                {
                    "cnpj": "55.666.777/0001-88",
                    "legal_name": "NINE CONTEXTO LTDA",
                    "trade_name": "Nine Contexto",
                    "status": "Ativa",
                    "email": "comercial@ninecontexto.com.br",
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
            scoped_list = create_list(conn, "Lista Nine", "Escopo workspace")
            add_companies_to_list(conn, scoped_list["id"], [company_id])

            scoped_dashboard = dashboard(conn)
            self.assertEqual(scoped_dashboard["active_workspace"]["id"], workspace["id"])
            self.assertEqual(scoped_dashboard["lists"], 1)
            self.assertEqual(scoped_dashboard["totals"]["companies"], 1)

            set_current_workspace(conn, 1)
            internal_lists = list_lists(conn)
            self.assertEqual([item["id"] for item in internal_lists], [internal_list["id"]])
            self.assertEqual(dashboard(conn)["lists"], 1)
            self.assertEqual(dashboard(conn)["totals"]["companies"], 0)
        finally:
            conn.close()

    def test_notifications_use_active_workspace(self):
        conn = connect()
        try:
            workspace = create_workspace(conn, {"name": "Real Grana"})
            set_current_workspace(conn, workspace["id"])
            conn.execute(
                """
                INSERT INTO handoffs (
                    org_id, lead_id, reply_classification_id, status, priority,
                    reason, context_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workspace["id"],
                    None,
                    None,
                    "pending",
                    "high",
                    "Lead quente no workspace ativo",
                    "{}",
                    now_iso(),
                ),
            )
            generated = generate_notifications(conn)
            self.assertEqual(generated["created"], 1)
            self.assertEqual(list_notifications(conn)["summary"]["pending"], 1)

            set_current_workspace(conn, 1)
            self.assertEqual(list_notifications(conn)["summary"]["pending"], 0)
        finally:
            conn.close()

    def test_okrs_use_active_workspace(self):
        conn = connect()
        try:
            workspace = create_workspace(conn, {"name": "Vagou Labs"})
            set_current_workspace(conn, workspace["id"])
            period_end = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
            objective = create_okr(
                conn,
                {
                    "title": "Validar OKR isolado",
                    "period_end": period_end,
                    "key_results": [
                        {"title": "Criar 1 handoff", "kpi_key": "pending_handoffs", "target_value": 1}
                    ],
                },
            )
            row = conn.execute("SELECT org_id FROM objectives WHERE id = ?", (objective["id"],)).fetchone()
            self.assertEqual(row["org_id"], workspace["id"])
            self.assertEqual(okr_dashboard(conn)["objectives"][0]["title"], "Validar OKR isolado")

            set_current_workspace(conn, 1)
            self.assertEqual(okr_dashboard(conn)["objectives"][0]["id"], "default")
        finally:
            conn.close()

    def test_audit_events_use_active_workspace(self):
        conn = connect()
        try:
            internal_list = create_list(conn, "Auditoria interna", "Evento interno")
            workspace = create_workspace(conn, {"name": "Auditoria Nine"})

            set_current_workspace(conn, workspace["id"])
            scoped_list = create_list(conn, "Auditoria Nine", "Evento isolado")
            scoped_entity_ids = {
                item["entity_id"]
                for item in audit_events(conn)
                if item["action"] == "create_list" and item["entity_type"] == "list"
            }
            self.assertIn(str(scoped_list["id"]), scoped_entity_ids)
            self.assertNotIn(str(internal_list["id"]), scoped_entity_ids)

            set_current_workspace(conn, 1)
            internal_entity_ids = {
                item["entity_id"]
                for item in audit_events(conn)
                if item["action"] == "create_list" and item["entity_type"] == "list"
            }
            self.assertIn(str(internal_list["id"]), internal_entity_ids)
            self.assertNotIn(str(scoped_list["id"]), internal_entity_ids)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
