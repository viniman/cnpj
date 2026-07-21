import json
import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    adjust_credit_wallet,
    create_api_key,
    create_workspace,
    get_active_api_key_by_token,
    list_api_keys,
    revoke_api_key,
    saas_account,
    set_current_workspace,
)


class SaasCredentialsTest(unittest.TestCase):
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

    def test_api_key_returns_token_once_and_lists_masked_data(self):
        conn = connect()
        try:
            created = create_api_key(conn, {"name": "Integracao local", "scopes": ["companies:read"]})
            self.assertTrue(created["token"].startswith("rc_local_"))
            self.assertEqual(created["status"], "active")
            self.assertEqual(created["scopes"], ["companies:read"])

            raw_row = conn.execute("SELECT token_hash, masked_token FROM api_keys WHERE id = ?", (created["id"],)).fetchone()
            self.assertNotEqual(raw_row["token_hash"], created["token"])
            self.assertNotIn(created["token"], raw_row["masked_token"])

            listed = list_api_keys(conn)["items"][0]
            self.assertNotIn("token", listed)
            self.assertNotIn("token_hash", listed)
            self.assertEqual(listed["masked_token"], created["masked_token"])

            active = get_active_api_key_by_token(conn, created["token"])
            self.assertEqual(active["id"], created["id"])
        finally:
            conn.close()

    def test_api_key_revocation_preserves_masked_record(self):
        conn = connect()
        try:
            created = create_api_key(conn, {"name": "Parceiro"})
            revoked = revoke_api_key(conn, created["id"], {"reason": "rotacao"})

            self.assertEqual(revoked["status"], "revoked")
            self.assertIsNotNone(revoked["revoked_at"])
            self.assertEqual(revoked["masked_token"], created["masked_token"])
            self.assertIsNone(get_active_api_key_by_token(conn, created["token"]))
        finally:
            conn.close()

    def test_credit_wallet_uses_append_only_ledger_and_blocks_negative_balance(self):
        conn = connect()
        try:
            initial = saas_account(conn)
            self.assertEqual(initial["wallet"]["balance"], 0)
            self.assertEqual(initial["transactions"], [])

            credit = adjust_credit_wallet(conn, {"amount": 10, "reason": "Credito manual"})
            self.assertEqual(credit["wallet"]["balance"], 10)
            self.assertEqual(credit["transaction"]["balance_after"], 10)

            debit = adjust_credit_wallet(conn, {"amount": -3, "reason": "Exportacao de teste"})
            self.assertEqual(debit["wallet"]["balance"], 7)
            self.assertEqual(debit["transaction"]["balance_after"], 7)

            with self.assertRaises(ValueError):
                adjust_credit_wallet(conn, {"amount": -8, "reason": "Sem saldo"})

            account = saas_account(conn)
            self.assertEqual(account["wallet"]["balance"], 7)
            self.assertEqual([item["amount"] for item in account["transactions"]], [-3, 10])
        finally:
            conn.close()

    def test_saas_credentials_are_scoped_to_active_workspace(self):
        conn = connect()
        try:
            internal_key = create_api_key(conn, {"name": "Interno"})
            adjust_credit_wallet(conn, {"amount": 12, "reason": "Saldo interno"})

            workspace = create_workspace(conn, {"name": "Nine SaaS"})
            set_current_workspace(conn, workspace["id"])
            scoped = saas_account(conn)
            self.assertEqual(scoped["wallet"]["balance"], 0)
            self.assertEqual(scoped["api_keys"], [])

            nine_key = create_api_key(conn, {"name": "Nine API"})
            adjust_credit_wallet(conn, {"amount": 5, "reason": "Saldo Nine"})
            scoped_after = saas_account(conn)
            self.assertEqual(scoped_after["wallet"]["balance"], 5)
            self.assertEqual([item["id"] for item in scoped_after["api_keys"]], [nine_key["id"]])

            set_current_workspace(conn, 1)
            internal = saas_account(conn)
            self.assertEqual(internal["wallet"]["balance"], 12)
            self.assertEqual([item["id"] for item in internal["api_keys"]], [internal_key["id"]])

            serialized = json.dumps(internal)
            self.assertNotIn(nine_key["masked_token"], serialized)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
