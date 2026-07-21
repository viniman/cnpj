import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from radar_cnpj.database import init_db
from radar_cnpj.server import RadarHandler
from radar_cnpj.services import (
    DEFAULT_API_RATE_LIMIT_PER_MINUTE,
    PUBLIC_COMPANY_SEARCH_COST,
    PUBLIC_COMPANY_SEARCH_SCOPE,
    public_openapi_spec,
)


class PublicOpenApiTest(unittest.TestCase):
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

    def test_openapi_spec_documents_public_company_search_contract(self):
        spec = public_openapi_spec()
        operation = spec["paths"]["/api/public/companies"]["get"]
        parameter_names = {item["name"] for item in operation["parameters"]}

        self.assertEqual(spec["openapi"], "3.0.3")
        self.assertIn("ApiKeyAuth", spec["components"]["securitySchemes"])
        self.assertIn("BearerAuth", spec["components"]["securitySchemes"])
        self.assertEqual(operation["x-required-scope"], PUBLIC_COMPANY_SEARCH_SCOPE)
        self.assertEqual(operation["x-credit-cost"], PUBLIC_COMPANY_SEARCH_COST)
        self.assertEqual(operation["x-rate-limit-default-per-minute"], DEFAULT_API_RATE_LIMIT_PER_MINUTE)
        self.assertTrue(
            {
                "query",
                "state",
                "city",
                "cnae",
                "status",
                "size",
                "sector",
                "has_email",
                "has_phone",
                "min_score",
                "limit",
                "offset",
            }.issubset(parameter_names)
        )
        for status_code in ("200", "401", "402", "403", "429"):
            self.assertIn(status_code, operation["responses"])
        self.assertIn("PublicCompanySearchResult", spec["components"]["schemas"])
        self.assertIn("PublicApiUsage", spec["components"]["schemas"])

    def test_openapi_route_returns_json_without_api_key(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), RadarHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            with urlopen(f"http://127.0.0.1:{port}/api/public/openapi.json", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["paths"]["/api/public/companies"]["get"]["x-credit-cost"], 1)
            self.assertEqual(response.status, 200)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
