import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.email_scoring import score_email
from radar_cnpj.services import score_email_record, upsert_company


class EmailScoringRulesTest(unittest.TestCase):
    def test_partner_match_scores_above_generic(self):
        partner = score_email("marina@novapilha.com.br", partner_names=["Marina Souza"])
        generic = score_email("contato@novapilha.com.br", partner_names=["Marina Souza"])
        self.assertEqual(partner["classification"], "partner_match")
        self.assertGreater(partner["score"], generic["score"])

    def test_disposable_domain_is_low_value(self):
        result = score_email("teste@mailinator.com")
        self.assertIn("disposable", result["labels"])
        self.assertLessEqual(result["score"], 20)

    def test_decision_maker_prefix_scores_high(self):
        result = score_email("ceo@empresa.com.br")
        self.assertEqual(result["classification"], "decision_maker")
        self.assertGreaterEqual(result["score"], 80)


class EmailScoringPersistenceTest(unittest.TestCase):
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

    def test_shared_email_is_flagged_and_persisted(self):
        companies = [
            ("11.222.333/0001-81", "ALFA LTDA"),
            ("22.333.444/0001-81", "BETA LTDA"),
            ("33.444.555/0001-81", "GAMA LTDA"),
        ]
        with connect() as conn:
            for cnpj, name in companies:
                upsert_company(
                    conn,
                    {
                        "cnpj": cnpj,
                        "legal_name": name,
                        "status": "Ativa",
                        "email": "contabil@assessoriacontabil.com.br",
                        "main_cnae_code": "7020400",
                    },
                    "Teste",
                    "fixture",
                    "Teste automatizado",
                )
            company = conn.execute("SELECT id FROM companies WHERE legal_name = 'ALFA LTDA'").fetchone()
            result = score_email_record(conn, "contabil@assessoriacontabil.com.br", company_id=company["id"])
            self.assertIn("shared_contact", result["labels"])
            self.assertLessEqual(result["score"], 25)
            saved = conn.execute(
                "SELECT classification, score FROM email_classifications WHERE company_id = ?",
                (company["id"],),
            ).fetchone()
            self.assertEqual(saved["classification"], "shared_contact")
            self.assertEqual(saved["score"], result["score"])


if __name__ == "__main__":
    unittest.main()

