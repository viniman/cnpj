import os
import tempfile
import unittest

from radar_cnpj.company_enrichment import (
    cache_lookup,
    cache_store,
    detect_technologies,
    digital_maturity,
    extract_emails,
    extract_phones,
    extract_social_links,
)
from radar_cnpj.database import connect, init_db
from radar_cnpj.services import enrich_company, get_company_enrichment, upsert_company


HTML = """
<html>
  <head>
    <meta name="generator" content="WordPress 6.5">
    <script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC123"></script>
    <script src="https://d335luupugsy2.cloudfront.net/js/rdstation-forms.js"></script>
  </head>
  <body>
    <a href="mailto:contato@novapilha.com.br">contato@novapilha.com.br</a>
    <a href="https://wa.me/5511987654321">WhatsApp</a>
    <a href="https://www.linkedin.com/company/novapilha">LinkedIn</a>
    <a href="https://instagram.com/novapilha">Instagram</a>
    Telefone: (11) 4000-1234
    <img src="/wp-content/uploads/logo.png">
  </body>
</html>
"""


class CompanyEnrichmentParserTest(unittest.TestCase):
    def test_extracts_public_contact_signals(self):
        self.assertEqual(extract_emails(HTML), ["contato@novapilha.com.br"])
        self.assertIn("11987654321", extract_phones(HTML))
        self.assertIn("1140001234", extract_phones(HTML))
        links = extract_social_links(HTML, "https://novapilha.com.br")
        self.assertIn("https://www.linkedin.com/company/novapilha", links)
        self.assertIn("https://instagram.com/novapilha", links)

    def test_detects_technology_stack(self):
        techs = detect_technologies({"Server": "cloudflare"}, HTML)
        self.assertIn("wordpress", techs)
        self.assertIn("google_tag_manager", techs)
        self.assertIn("rd_station", techs)
        self.assertIn("cloudflare", techs)

    def test_scores_digital_maturity_with_explanations(self):
        score, reasons, confidence = digital_maturity(
            "https://novapilha.com.br",
            emails=["contato@novapilha.com.br"],
            phones=["11987654321"],
            social_links=["https://www.linkedin.com/company/novapilha"],
            technologies=["wordpress", "google_tag_manager", "rd_station"],
        )
        self.assertGreaterEqual(score, 80)
        self.assertEqual(confidence, "high")
        self.assertTrue(any("Analytics" in reason for reason in reasons))


class CompanyEnrichmentPersistenceTest(unittest.TestCase):
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

    def test_enrich_company_from_provided_html(self):
        conn = connect()
        try:
            company_id = upsert_company(
                conn,
                {
                    "cnpj": "11.222.333/0001-81",
                    "legal_name": "NOVA PILHA LTDA",
                    "trade_name": "Nova Pilha",
                    "status": "Ativa",
                    "email": "contato@novapilha.com.br",
                    "main_cnae_code": "6201501",
                },
                "Teste",
                "fixture",
                "Teste automatizado",
            )
            result = enrich_company(
                conn,
                company_id,
                source_url="https://novapilha.com.br",
                html=HTML,
            )
            self.assertEqual(result["company_id"], company_id)
            self.assertEqual(result["detected_domain"], "novapilha.com.br")
            self.assertIn("contato@novapilha.com.br", result["emails"])
            self.assertIn("wordpress", result["technologies"])

            saved = get_company_enrichment(conn, company_id)
            self.assertEqual(saved["digital_maturity_score"], result["digital_maturity_score"])
            self.assertEqual(saved["source_type"], "provided_html")
        finally:
            conn.close()

    def test_scraping_cache_reuses_unexpired_url(self):
        conn = connect()
        try:
            cache_store(
                conn,
                {
                    "url": "https://novapilha.com.br",
                    "status_code": 200,
                    "headers": {"Server": "cloudflare"},
                    "body_hash": "fixture-hash",
                    "body_text": HTML,
                },
                ttl_days=1,
            )
            cached = cache_lookup(conn, "https://novapilha.com.br/")
            self.assertIsNotNone(cached)
            self.assertEqual(cached["body_text"], HTML)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
