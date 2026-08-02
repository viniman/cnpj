import json
import os
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def read_text(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def read_json(path):
    return json.loads(read_text(path))


class NextNestFoundationTest(unittest.TestCase):
    def test_root_package_defines_workspaces(self):
        package = read_json("package.json")

        self.assertEqual(package["name"], "radar-cnpj-platform")
        self.assertIn("apps/api", package["workspaces"])
        self.assertIn("apps/web", package["workspaces"])
        self.assertIn("dev:api", package["scripts"])
        self.assertIn("dev:web", package["scripts"])

    def test_api_scaffold_exists(self):
        package = read_json("apps/api/package.json")
        schema = read_text("apps/api/prisma/schema.prisma")
        module = read_text("apps/api/src/app.module.ts")

        self.assertEqual(package["name"], "@radar-cnpj/api")
        self.assertIn("@nestjs/core", package["dependencies"])
        self.assertIn("provider = \"postgresql\"", schema)
        self.assertIn("HealthController", module)
        self.assertIn("ReceitaController", module)

    def test_web_scaffold_exists(self):
        package = read_json("apps/web/package.json")
        page = read_text("apps/web/app/page.tsx")

        self.assertEqual(package["name"], "@radar-cnpj/web")
        self.assertIn("next", package["dependencies"])
        self.assertIn("getApiStatus", page)
        self.assertIn("Radar CNPJ", page)

    def test_docs_explain_layer_ownership(self):
        docs = read_text("docs/NEXT_NEST_FOUNDATION.md")

        self.assertIn("Python atual", docs)
        self.assertIn("apps/api", docs)
        self.assertIn("apps/web", docs)
        self.assertIn("receita_staging", docs)


if __name__ == "__main__":
    unittest.main()
