import unittest

from radar_cnpj.email_hygiene import classify_email


class EmailHygieneTest(unittest.TestCase):
    def test_invalid_email(self):
        result = classify_email("nao-e-email")
        self.assertEqual(result["classification"], "Invalido")
        self.assertEqual(result["score"], 0)

    def test_generic_corporate_email(self):
        result = classify_email("contato@empresa.com.br")
        self.assertEqual(result["classification"], "Generico")
        self.assertIn("Corporativo", result["labels"])

    def test_suppression_wins(self):
        result = classify_email("vendas@empresa.com.br", {"vendas@empresa.com.br"})
        self.assertEqual(result["classification"], "Suprimido")
        self.assertLessEqual(result["score"], 5)


if __name__ == "__main__":
    unittest.main()

