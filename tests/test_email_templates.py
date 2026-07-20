import os
import tempfile
import unittest

from radar_cnpj.database import connect, init_db
from radar_cnpj.email_templates import render_template
from radar_cnpj.services import (
    create_email_template,
    create_email_template_version,
    create_workspace,
    get_email_template,
    list_email_templates,
    render_email_template,
    set_current_workspace,
    upsert_company,
)


class EmailTemplateRenderRulesTest(unittest.TestCase):
    def test_render_injects_footer_and_reports_missing_variables(self):
        rendered = render_template(
            "Ola {{nome_empresa}}",
            "Vi que {{nome_empresa}} atua em {{cidade}}. {{variavel_extra}}",
            {"nome_empresa": "Nova Pilha", "cidade": "Sao Paulo"},
        )
        self.assertEqual(rendered["subject"], "Ola Nova Pilha")
        self.assertIn("Voce recebeu este contato", rendered["body"])
        self.assertIn("variavel_extra", rendered["missing_variables"])

    def test_system_compliance_variables_are_not_editable(self):
        with self.assertRaises(ValueError):
            render_template(
                "Teste",
                "Clique em {{unsubscribe_url}}",
                {},
            )


class EmailTemplatePersistenceTest(unittest.TestCase):
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

    def seed_company(self, conn):
        return upsert_company(
            conn,
            {
                "cnpj": "11.222.333/0001-81",
                "legal_name": "NOVA PILHA LTDA",
                "trade_name": "Nova Pilha",
                "status": "Ativa",
                "email": "comercial@novapilha.com.br",
                "main_cnae_code": "6201501",
                "main_cnae_description": "Software sob encomenda",
                "city": "Sao Paulo",
                "state": "SP",
                "capital_social": 200000,
                "partners": "Marina Souza|Socio-administrador|2022-01-01",
            },
            "Teste",
            "fixture",
            "Teste automatizado",
        )

    def test_create_template_and_version_history(self):
        conn = connect()
        try:
            template = create_email_template(
                conn,
                {
                    "name": "Primeiro contato",
                    "purpose": "first_contact",
                    "subject": "Ideia rapida para {{nome_empresa}}",
                    "body": "Vi que a {{nome_empresa}} {{motivo_contato}}.",
                },
            )
            self.assertEqual(template["active_version"]["version_number"], 1)
            self.assertEqual(template["active_version"]["variables"], ["nome_empresa", "motivo_contato"])

            updated = create_email_template_version(
                conn,
                template["id"],
                {
                    "subject": "Outro teste para {{nome_empresa}}",
                    "body": "Ola {{nome_contato}}, podemos falar sobre {{cidade}}?",
                },
            )
            self.assertEqual(updated["active_version"]["version_number"], 2)
            self.assertEqual(len(updated["versions"]), 2)
            old = [version for version in updated["versions"] if version["version_number"] == 1][0]
            self.assertEqual(old["is_active"], 0)
        finally:
            conn.close()

    def test_render_template_with_company_context(self):
        conn = connect()
        try:
            company_id = self.seed_company(conn)
            template = create_email_template(
                conn,
                {
                    "name": "Contexto empresa",
                    "purpose": "first_contact",
                    "subject": "Ideia para {{nome_empresa}} em {{cidade}}",
                    "body": "Ola {{nome_contato}}, vi que a {{razao_social}} {{motivo_contato}}. CTA: {{cta_url}}",
                },
            )
            rendered = render_email_template(
                conn,
                {
                    "template_id": template["id"],
                    "company_id": company_id,
                    "cta_url": "https://usevagou.com.br/contato",
                },
            )
            self.assertIn("Nova Pilha", rendered["subject"])
            self.assertIn("Marina Souza", rendered["body"])
            self.assertIn("https://usevagou.com.br/contato", rendered["body"])
            self.assertIn("Voce recebeu este contato", rendered["body"])
            self.assertEqual(rendered["missing_variables"], [])
        finally:
            conn.close()

    def test_get_template_returns_active_version(self):
        conn = connect()
        try:
            template = create_email_template(
                conn,
                {
                    "name": "Busca ativa",
                    "purpose": "follow_up",
                    "subject": "Follow-up {{nome_empresa}}",
                    "body": "Retomando o contato.",
                },
            )
            saved = get_email_template(conn, template["id"])
            self.assertEqual(saved["active_version"]["version_number"], 1)
            self.assertEqual(saved["purpose"], "follow_up")
        finally:
            conn.close()

    def test_templates_follow_active_workspace(self):
        conn = connect()
        try:
            internal = create_email_template(
                conn,
                {
                    "name": "Template interno",
                    "purpose": "first_contact",
                    "subject": "Ola {{nome_empresa}}",
                    "body": "Mensagem interna para {{nome_empresa}}.",
                },
            )
            workspace = create_workspace(conn, {"name": "Nine Templates"})
            set_current_workspace(conn, workspace["id"])

            self.assertEqual(list_email_templates(conn)["items"], [])
            self.assertIsNone(get_email_template(conn, internal["id"]))
            with self.assertRaises(ValueError):
                create_email_template_version(conn, internal["id"], {"body": "Nova versao indevida"})
            with self.assertRaises(ValueError):
                render_email_template(conn, {"template_id": internal["id"], "context": {"nome_empresa": "Nine"}})
            with self.assertRaises(ValueError):
                render_email_template(
                    conn,
                    {
                        "template_version_id": internal["active_version"]["id"],
                        "context": {"nome_empresa": "Nine"},
                    },
                )

            scoped = create_email_template(
                conn,
                {
                    "name": "Template Nine",
                    "purpose": "follow_up",
                    "subject": "Nine para {{nome_empresa}}",
                    "body": "Copy do workspace Nine.",
                },
            )
            self.assertEqual(scoped["org_id"], workspace["id"])
            self.assertEqual([item["id"] for item in list_email_templates(conn)["items"]], [scoped["id"]])
            rendered = render_email_template(conn, {"template_id": scoped["id"], "context": {"nome_empresa": "Acme"}})
            self.assertIn("Voce recebeu este contato", rendered["body"])

            set_current_workspace(conn, 1)
            self.assertEqual([item["id"] for item in list_email_templates(conn)["items"]], [internal["id"]])
            self.assertIsNone(get_email_template(conn, scoped["id"]))
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

