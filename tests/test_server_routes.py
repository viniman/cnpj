import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from radar_cnpj.database import init_db
from radar_cnpj.server import RadarHandler


class ServerRouteTest(unittest.TestCase):
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

    def test_sequence_journeys_route_is_not_treated_as_sequence_id(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), RadarHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            with urlopen(f"http://127.0.0.1:{port}/api/sequences/journeys", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload, {"items": []})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_scoring_config_version_diff_route_is_available(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), RadarHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            with urlopen(f"http://127.0.0.1:{port}/api/scoring/config", timeout=5):
                pass
            request = Request(
                f"http://127.0.0.1:{port}/api/scoring/config",
                data=json.dumps(
                    {"email_prefix_rules": {"rh": {"area": "decisor RH", "score": 82, "label": "decision_maker"}}}
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5):
                pass
            with urlopen(f"http://127.0.0.1:{port}/api/scoring/config-versions?type=email", timeout=5) as response:
                versions = json.loads(response.read().decode("utf-8"))["items"]
            original = [item for item in versions if item["version_number"] == 1][0]

            with urlopen(f"http://127.0.0.1:{port}/api/scoring/config-versions/{original['id']}/diff", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            self.assertEqual(payload["config_type"], "email")
            self.assertTrue(payload["summary"]["has_changes"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
