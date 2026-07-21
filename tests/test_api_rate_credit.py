import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.services import (
    ApiAccessError,
    adjust_credit_wallet,
    create_api_key,
    create_workspace,
    public_search_companies,
    saas_account,
    set_current_workspace,
    upsert_company,
)


class ApiRateCreditTest(unittest.TestCase):
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

    def seed_company(self, conn, name="API PUBLICA LTDA", email="api@publica.com.br", cnpj="12.345.678/0001-95"):
        return upsert_company(
            conn,
            {
                "cnpj": cnpj,
                "legal_name": name,
                "trade_name": name.split()[0],
                "status": "Ativa",
                "email": email,
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software sob encomenda",
                "city": "Sao Paulo",
                "state": "SP",
                "capital_social": 250000,
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )

    def assert_api_error(self, status_code, fn, *args, **kwargs):
        with self.assertRaises(ApiAccessError) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.status_code, status_code)

    def test_public_company_search_requires_token(self):
        conn = connect()
        try:
            self.assert_api_error(401, public_search_companies, conn, "", {"limit": 1})
        finally:
            conn.close()

    def test_public_company_search_blocks_missing_scope_without_debit(self):
        conn = connect()
        try:
            key = create_api_key(conn, {"name": "Email only", "scopes": ["emails:read"]})
            adjust_credit_wallet(conn, {"amount": 5, "reason": "Credito teste"})

            self.assert_api_error(403, public_search_companies, conn, key["token"], {"limit": 1})

            account = saas_account(conn)
            self.assertEqual(account["wallet"]["balance"], 5)
            self.assertEqual(account["usage_events"][0]["status"], "blocked_scope")
            self.assertEqual(account["transactions"][0]["amount"], 5)
        finally:
            conn.close()

    def test_public_company_search_blocks_insufficient_credit_without_debit(self):
        conn = connect()
        try:
            key = create_api_key(conn, {"name": "Consulta"})
            self.seed_company(conn)

            self.assert_api_error(402, public_search_companies, conn, key["token"], {"limit": 1})

            account = saas_account(conn)
            self.assertEqual(account["wallet"]["balance"], 0)
            self.assertEqual(account["usage_events"][0]["status"], "blocked_credit")
            self.assertEqual(account["transactions"], [])
        finally:
            conn.close()

    def test_public_company_search_debits_credit_and_uses_filters(self):
        conn = connect()
        try:
            key = create_api_key(conn, {"name": "Busca"})
            adjust_credit_wallet(conn, {"amount": 3, "reason": "Credito teste"})
            self.seed_company(conn, name="ALVO API LTDA", email="contato@alvoapi.com.br", cnpj="12.345.678/0001-95")
            self.seed_company(conn, name="OUTRA API LTDA", email="contato@outraapi.com.br", cnpj="98.765.432/0001-10")

            result = public_search_companies(conn, key["token"], {"query": "ALVO", "limit": 5})

            self.assertEqual(result["total"], 1)
            self.assertEqual(result["items"][0]["legal_name"], "ALVO API LTDA")
            self.assertEqual(result["usage"]["cost"], 1)
            self.assertEqual(result["usage"]["balance_after"], 2)

            account = saas_account(conn)
            self.assertEqual(account["wallet"]["balance"], 2)
            self.assertEqual(account["usage_events"][0]["status"], "ok")
            self.assertEqual(account["transactions"][0]["amount"], -1)
        finally:
            conn.close()

    def test_public_company_search_rate_limits_per_key(self):
        conn = connect()
        try:
            key = create_api_key(conn, {"name": "Limitada"})
            adjust_credit_wallet(conn, {"amount": 5, "reason": "Credito teste"})
            self.seed_company(conn)

            public_search_companies(conn, key["token"], {"limit": 1}, rate_limit_per_minute=1)
            self.assert_api_error(
                429,
                public_search_companies,
                conn,
                key["token"],
                {"limit": 1},
                rate_limit_per_minute=1,
            )

            account = saas_account(conn)
            self.assertEqual(account["wallet"]["balance"], 4)
            self.assertEqual([item["status"] for item in account["usage_events"][:2]], ["blocked_rate_limit", "ok"])
        finally:
            conn.close()

    def test_public_api_uses_key_workspace_not_active_workspace(self):
        conn = connect()
        try:
            internal_key = create_api_key(conn, {"name": "Interna"})
            adjust_credit_wallet(conn, {"amount": 2, "reason": "Credito interno"})
            self.seed_company(conn)

            workspace = create_workspace(conn, {"name": "Nine API"})
            set_current_workspace(conn, workspace["id"])
            self.assertEqual(saas_account(conn)["wallet"]["balance"], 0)

            result = public_search_companies(conn, internal_key["token"], {"limit": 1})
            self.assertEqual(result["usage"]["balance_after"], 1)
            self.assertEqual(saas_account(conn)["wallet"]["balance"], 0)

            set_current_workspace(conn, 1)
            self.assertEqual(saas_account(conn)["wallet"]["balance"], 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
