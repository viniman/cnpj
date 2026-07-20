import re


VARIABLE_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

SYSTEM_VARIABLES = {"unsubscribe_url", "privacy_url"}

SUPPORTED_VARIABLES = {
    "nome_empresa",
    "razao_social",
    "cnpj",
    "cidade",
    "estado",
    "cnae_codigo",
    "cnae_descricao",
    "setor",
    "segmento",
    "nome_contato",
    "email_empresa",
    "motivo_contato",
    "cta_url",
}

DEFAULT_UNSUBSCRIBE_URL = "http://127.0.0.1:8000/unsubscribe"
DEFAULT_PRIVACY_URL = "http://127.0.0.1:8000/privacy"

COMPLIANCE_FOOTER_TEMPLATE = """
--
Voce recebeu este contato em contexto B2B, a partir de dados publicos de CNPJ
e/ou canais publicados pela propria empresa. Para nao receber novos contatos,
responda "remover" ou acesse {{unsubscribe_url}}. Politica de privacidade:
{{privacy_url}}.
""".strip()


class TemplateValidationError(ValueError):
    pass


def extract_variables(*texts):
    variables = []
    seen = set()
    for text in texts:
        for match in VARIABLE_RE.findall(text or ""):
            name = match.strip()
            if name not in seen:
                variables.append(name)
                seen.add(name)
    return variables


def validate_editable_template(subject, body):
    variables = set(extract_variables(subject, body))
    blocked = sorted(variables & SYSTEM_VARIABLES)
    if blocked:
        raise TemplateValidationError(
            "Variaveis de compliance nao podem ser editadas no template: %s" % ", ".join(blocked)
        )


def first_partner_name(partners):
    for partner in partners or []:
        name = (partner.get("name") if isinstance(partner, dict) else "") or ""
        if name.strip():
            return name.strip()
    return ""


def build_company_template_context(company, partners=None, cta_url=""):
    company = company or {}
    company_name = company.get("trade_name") or company.get("legal_name") or ""
    city = company.get("city") or ""
    cnae = company.get("main_cnae_description") or company.get("main_cnae_code") or ""
    reason_bits = []
    if cnae:
        reason_bits.append("atua em %s" % cnae)
    if city:
        reason_bits.append("esta em %s" % city)
    if company.get("source_name"):
        reason_bits.append("consta em base publica de CNPJ")
    motivo = ", ".join(reason_bits) if reason_bits else "tem perfil aderente ao nosso estudo B2B"
    return {
        "nome_empresa": company_name,
        "razao_social": company.get("legal_name") or "",
        "cnpj": company.get("cnpj") or "",
        "cidade": city,
        "estado": company.get("state") or "",
        "cnae_codigo": company.get("main_cnae_code") or "",
        "cnae_descricao": company.get("main_cnae_description") or "",
        "setor": company.get("sector") or "",
        "segmento": company.get("segment") or "",
        "nome_contato": first_partner_name(partners),
        "email_empresa": company.get("email") or "",
        "motivo_contato": motivo,
        "cta_url": cta_url or "",
    }


def render_text(template_text, context):
    missing = []

    def replace(match):
        name = match.group(1).strip()
        value = context.get(name)
        if value is None or value == "":
            if name not in missing:
                missing.append(name)
            return ""
        return str(value)

    return VARIABLE_RE.sub(replace, template_text or ""), missing


def render_footer(unsubscribe_url=None, privacy_url=None):
    context = {
        "unsubscribe_url": unsubscribe_url or DEFAULT_UNSUBSCRIBE_URL,
        "privacy_url": privacy_url or DEFAULT_PRIVACY_URL,
    }
    footer, _missing = render_text(COMPLIANCE_FOOTER_TEMPLATE, context)
    return footer


def render_template(subject, body, company_context=None, unsubscribe_url=None, privacy_url=None):
    validate_editable_template(subject, body)
    context = company_context or {}
    rendered_subject, missing_subject = render_text(subject, context)
    rendered_body_without_footer, missing_body = render_text(body, context)
    footer = render_footer(unsubscribe_url=unsubscribe_url, privacy_url=privacy_url)
    rendered_body = "%s\n\n%s" % (rendered_body_without_footer.rstrip(), footer)
    missing = []
    for item in missing_subject + missing_body:
        if item not in missing:
            missing.append(item)
    return {
        "subject": rendered_subject,
        "body_without_footer": rendered_body_without_footer,
        "footer": footer,
        "body": rendered_body,
        "missing_variables": missing,
        "used_variables": extract_variables(subject, body),
    }

