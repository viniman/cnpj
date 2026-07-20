import os
import tempfile
import unittest

from radar_cnpj.database import init_db
from radar_cnpj.services import seed_sample, search_companies


class ServicesTest(unittest.TestCase):
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

    def test_seed_and_search(self):
        from radar_cnpj.database import connect

        with connect() as conn:
            result = seed_sample(conn)
            self.assertEqual(result["status"], "completed")
            data = search_companies(conn, {"state": "SP", "has_email": "1"})
            self.assertGreaterEqual(data["total"], 1)


if __name__ == "__main__":
    unittest.main()

