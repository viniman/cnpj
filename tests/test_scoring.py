import unittest

from radar_cnpj.scoring import infer_sector, score_company


class ScoringTest(unittest.TestCase):
    def test_infer_technology_sector(self):
        sector, segment = infer_sector("6201501", "Software")
        self.assertEqual(sector, "Tecnologia")
        self.assertIn("Software", segment)

    def test_score_rewards_active_company_with_contact(self):
        score, reasons = score_company(
            {
                "status": "Ativa",
                "email": "contato@empresa.com.br",
                "phone": "(11) 4000-0000",
                "size": "EPP",
                "capital_social": "200000",
                "opening_date": "2023-01-01",
                "main_cnae_code": "6201501",
            }
        )
        self.assertGreaterEqual(score, 80)
        self.assertTrue(any("empresa ativa" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()

