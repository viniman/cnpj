import re
import unicodedata

from .email_hygiene import DISPOSABLE_DOMAINS, EMAIL_RE, PERSONAL_DOMAINS, classify_email, normalize_email


ALGORITHM_VERSION = "email-score-v1"

PREFIX_RULES = {
    "contato": ("atendimento generico", 25, "generic_inbox"),
    "atendimento": ("atendimento generico", 25, "generic_inbox"),
    "sac": ("atendimento generico", 20, "generic_inbox"),
    "suporte": ("atendimento generico", 25, "generic_inbox"),
    "info": ("atendimento generico", 25, "generic_inbox"),
    "administrativo": ("administrativo", 30, "role_inbox"),
    "admin": ("administrativo", 30, "role_inbox"),
    "contabil": ("contabil/fiscal", 10, "role_inbox"),
    "contabilidade": ("contabil/fiscal", 10, "role_inbox"),
    "fiscal": ("contabil/fiscal", 12, "role_inbox"),
    "escritorio": ("contabil/fiscal", 10, "role_inbox"),
    "financeiro": ("financeiro", 35, "role_inbox"),
    "cobranca": ("financeiro", 30, "role_inbox"),
    "contas": ("financeiro", 30, "role_inbox"),
    "rh": ("recursos humanos", 35, "role_inbox"),
    "recursoshumanos": ("recursos humanos", 35, "role_inbox"),
    "vagas": ("recursos humanos", 25, "role_inbox"),
    "comercial": ("comercial", 55, "role_inbox"),
    "vendas": ("comercial", 55, "role_inbox"),
    "sales": ("comercial", 55, "role_inbox"),
    "juridico": ("juridico", 25, "role_inbox"),
    "compliance": ("juridico", 25, "role_inbox"),
    "diretoria": ("decisor", 80, "decision_maker"),
    "presidencia": ("decisor", 80, "decision_maker"),
    "ceo": ("decisor", 85, "decision_maker"),
    "socio": ("decisor", 80, "decision_maker"),
    "dono": ("decisor", 80, "decision_maker"),
    "ti": ("tecnologia", 45, "role_inbox"),
    "dev": ("tecnologia", 45, "role_inbox"),
    "sistemas": ("tecnologia", 45, "role_inbox"),
}

SHARED_DOMAIN_HINTS = {
    "contab": "contabil",
    "contabil": "contabil",
    "assessoria": "assessoria",
    "consultoria": "consultoria",
    "adv": "juridico",
    "jurid": "juridico",
}

COMMON_PROVIDER_DOMAINS = PERSONAL_DOMAINS | {
    "gmail.com.br",
    "terra.com.br",
    "r7.com",
    "globo.com",
    "me.com",
}


def ascii_key(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.lower())


def local_tokens(local):
    return [token for token in re.split(r"[._+\-]+", local or "") if token]


def is_nominal_local(local):
    tokens = local_tokens(local)
    if len(tokens) >= 2 and all(len(token) >= 2 for token in tokens[:2]):
        return True
    if len(tokens) == 1:
        token = tokens[0]
        if token in PREFIX_RULES:
            return False
        if any(ch.isdigit() for ch in token):
            return False
        return 4 <= len(token) <= 16
    return False


def partner_match(local, partner_names):
    local_key = ascii_key(local)
    local_parts = [ascii_key(part) for part in local_tokens(local)]
    for name in partner_names or []:
        tokens = [ascii_key(token) for token in str(name).split() if len(ascii_key(token)) >= 3]
        if not tokens:
            continue
        if local_key in tokens:
            return True
        if len(tokens) >= 2 and local_key in (tokens[0] + tokens[-1], tokens[0] + "." + tokens[-1]):
            return True
        if local_parts and all(part in tokens for part in local_parts[:2]):
            return True
    return False


def infer_shared_domain_type(domain):
    domain_key = ascii_key(domain)
    for needle, inferred in SHARED_DOMAIN_HINTS.items():
        if needle in domain_key:
            return inferred
    return "prestador compartilhado"


def score_email(
    email,
    partner_names=None,
    company_domain=None,
    hygiene_result=None,
    same_email_companies=1,
    same_domain_companies=1,
    known_shared_domains=None,
    suppression_set=None,
    opt_out_set=None,
    prefix_rules=None,
    prefix_rules_source="default",
):
    normalized = normalize_email(email)
    known_shared_domains = known_shared_domains or set()
    active_prefix_rules = prefix_rules or PREFIX_RULES
    partner_names = partner_names or []
    labels = []
    reasons = []
    score = 50
    area = "nao classificado"

    if not normalized or not EMAIL_RE.match(normalized):
        return result(normalized, "", "", area, "invalid", ["invalid"], 0, ["Formato de email invalido"], 0, 0)

    local, domain = normalized.split("@", 1)
    local_prefix = local_tokens(local)[0] if local_tokens(local) else local
    hygiene = hygiene_result or classify_email(normalized, suppression_set, opt_out_set)

    if hygiene["classification"] in ("Invalido", "Opt-out"):
        labels.append("suppressed" if hygiene["classification"] == "Opt-out" else "invalid")
        reasons.extend(hygiene.get("reasons") or [])
        return result(
            normalized,
            local,
            domain,
            area,
            labels[0],
            labels,
            0,
            reasons,
            same_email_companies,
            same_domain_companies,
        )

    if hygiene["classification"] == "Suprimido":
        labels.append("suppressed")
        reasons.append("Email esta na lista de supressao")
        return result(normalized, local, domain, area, "suppressed", labels, 0, reasons, same_email_companies, same_domain_companies)

    if local_prefix in active_prefix_rules:
        area, score, label = active_prefix_rules[local_prefix]
        labels.append(label)
        reasons.append("Prefixo '%s' indica area: %s" % (local_prefix, area))
        if prefix_rules_source != "default":
            reasons.append("Regra de prefixo do workspace aplicada")
    elif is_nominal_local(local):
        labels.append("nominal")
        score += 15
        area = "nominal/pessoa"
        reasons.append("Local-part aparenta ser nome de pessoa")

    if domain in DISPOSABLE_DOMAINS:
        labels.append("disposable")
        score -= 60
        reasons.append("Dominio descartavel")

    if domain in PERSONAL_DOMAINS:
        labels.append("personal_domain")
        score -= 25
        reasons.append("Dominio de e-mail pessoal")

    if company_domain and ascii_key(company_domain) == ascii_key(domain):
        labels.append("company_domain_match")
        score += 20
        reasons.append("Dominio do e-mail bate com dominio da empresa")

    if partner_match(local, partner_names):
        labels.append("partner_match")
        score += 30
        reasons.append("Local-part bate com nome de socio/administrador")

    same_email_companies = int(same_email_companies or 0)
    same_domain_companies = int(same_domain_companies or 0)
    is_common_provider = domain in COMMON_PROVIDER_DOMAINS

    if same_email_companies >= 3:
        labels.append("shared_contact")
        score -= 55
        reasons.append("Mesmo e-mail aparece em %s CNPJs distintos" % same_email_companies)

    if domain in known_shared_domains:
        labels.append("known_shared_domain")
        score = min(score, 25)
        reasons.append("Dominio ja marcado como contato terceirizado")
    elif same_domain_companies >= 5 and not is_common_provider:
        labels.append("shared_domain")
        score -= 35
        reasons.append("Dominio aparece em %s CNPJs distintos" % same_domain_companies)

    if hygiene["classification"] == "Suspeito":
        score -= 30
        labels.append("risky_hygiene")
        reasons.append("Higiene marcou o e-mail como suspeito")

    if not labels:
        labels.append("corporate_unknown")
        reasons.append("E-mail corporativo sem area inferida")

    score = max(0, min(100, int(score)))
    primary = primary_classification(labels, score)
    scoring = result(normalized, local, domain, area, primary, labels, score, reasons, same_email_companies, same_domain_companies)
    scoring["prefix_rule_source"] = prefix_rules_source if local_prefix in active_prefix_rules else "heuristic"
    scoring["prefix_rule_key"] = local_prefix if local_prefix in active_prefix_rules else ""
    return scoring


def primary_classification(labels, score):
    priority = [
        ("invalid", "invalid"),
        ("suppressed", "suppressed"),
        ("disposable", "disposable"),
        ("known_shared_domain", "shared_domain"),
        ("shared_contact", "shared_contact"),
        ("shared_domain", "shared_domain"),
        ("partner_match", "partner_match"),
        ("decision_maker", "decision_maker"),
        ("nominal", "nominal"),
        ("role_inbox", "role_inbox"),
        ("generic_inbox", "generic_inbox"),
        ("personal_domain", "personal_domain"),
    ]
    for label, classification in priority:
        if label in labels:
            return classification
    if score >= 70:
        return "high_value"
    if score >= 40:
        return "medium_value"
    return "low_value"


def result(email, local, domain, area, classification, labels, score, reasons, same_email_companies, same_domain_companies):
    return {
        "email": email,
        "local": local,
        "domain": domain,
        "area": area,
        "classification": classification,
        "labels": labels,
        "score": score,
        "reasons": reasons,
        "shared_company_count": int(same_email_companies or 0),
        "shared_domain_count": int(same_domain_companies or 0),
        "algorithm_version": ALGORITHM_VERSION,
        "shared_domain_type": infer_shared_domain_type(domain) if domain else "",
    }

