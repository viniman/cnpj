import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    apply_saas_plan_subscription,
    create_workspace,
    list_saas_plans,
    saas_account,
    set_current_workspace,
)


class SaasPlanModelTest(unittest.TestCase):
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

    def test_default_saas_plans_are_idempotent(self):
        conn = connect()
        try:
            first = list_saas_plans(conn)["items"]
            second = list_saas_plans(conn)["items"]
            codes = [item["code"] for item in second]

            self.assertEqual(len(first), len(second))
            self.assertEqual(sorted(codes), ["free", "growth", "internal", "scale", "starter"])
            self.assertEqual(len(codes), len(set(codes)))
            self.assertTrue(next(item for item in second if item["code"] == "growth")["allow_agent"])
        finally:
            conn.close()

    def test_apply_plan_creates_subscription_and_credits_ledger(self):
        conn = connect()
        try:
            result = apply_saas_plan_subscription(conn, {"plan_code": "starter", "note": "Validar preco"})
            account = saas_account(conn)

            self.assertEqual(result["plan"]["code"], "starter")
            self.assertEqual(account["subscription"]["plan"]["code"], "starter")
            self.assertEqual(account["wallet"]["plan_name"], "starter")
            self.assertEqual(account["wallet"]["balance"], 1000)
            self.assertEqual(account["transactions"][0]["amount"], 1000)
            self.assertEqual(account["transactions"][0]["reference_type"], "saas_plan_subscription")
            self.assertEqual(account["transactions"][0]["metadata"]["plan_code"], "starter")
        finally:
            conn.close()

    def test_switching_plan_cancels_previous_subscription(self):
        conn = connect()
        try:
            first = apply_saas_plan_subscription(conn, {"plan_code": "starter"})
            second = apply_saas_plan_subscription(conn, {"plan_code": "growth"})

            previous = conn.execute(
                "SELECT status, canceled_at FROM workspace_plan_subscriptions WHERE id = ?",
                (first["subscription"]["id"],),
            ).fetchone()
            active_count = conn.execute(
                "SELECT COUNT(*) AS total FROM workspace_plan_subscriptions WHERE org_id = 1 AND status = 'active'"
            ).fetchone()["total"]
            account = saas_account(conn)

            self.assertEqual(second["subscription"]["plan"]["code"], "growth")
            self.assertEqual(previous["status"], "canceled")
            self.assertIsNotNone(previous["canceled_at"])
            self.assertEqual(active_count, 1)
            self.assertEqual(account["wallet"]["balance"], 6000)
        finally:
            conn.close()

    def test_archived_plan_cannot_be_applied(self):
        conn = connect()
        try:
            list_saas_plans(conn)
            conn.execute("UPDATE saas_plans SET status = 'archived' WHERE code = 'starter'")

            with self.assertRaises(ValueError):
                apply_saas_plan_subscription(conn, {"plan_code": "starter"})

            self.assertIsNone(saas_account(conn)["subscription"])
            self.assertEqual(saas_account(conn)["wallet"]["balance"], 0)
        finally:
            conn.close()

    def test_saas_plan_subscription_is_scoped_to_active_workspace(self):
        conn = connect()
        try:
            apply_saas_plan_subscription(conn, {"plan_code": "starter"})
            workspace = create_workspace(conn, {"name": "Nine Plans"})
            set_current_workspace(conn, workspace["id"])

            scoped_before = saas_account(conn)
            self.assertIsNone(scoped_before["subscription"])
            self.assertEqual(scoped_before["wallet"]["balance"], 0)

            apply_saas_plan_subscription(conn, {"plan_code": "growth"})
            scoped_after = saas_account(conn)
            self.assertEqual(scoped_after["subscription"]["plan"]["code"], "growth")
            self.assertEqual(scoped_after["wallet"]["balance"], 5000)

            set_current_workspace(conn, 1)
            internal = saas_account(conn)
            self.assertEqual(internal["subscription"]["plan"]["code"], "starter")
            self.assertEqual(internal["wallet"]["balance"], 1000)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
