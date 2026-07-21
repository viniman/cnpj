from datetime import datetime


SECTOR_RULES = [
    (("62", "63"), "Tecnologia", "Software, dados e servicos digitais"),
    (("86", "87", "88"), "Saude", "Saude, clinicas e cuidado"),
    (("41", "42", "43"), "Construcao", "Construcao e infraestrutura"),
    (("45", "46", "47"), "Comercio", "Comercio atacadista e varejista"),
    (("49", "50", "51", "52", "53"), "Logistica", "Transporte e armazenagem"),
    (("55", "56"), "Hospitalidade", "Hospedagem e alimentacao"),
    (("64", "65", "66"), "Financeiro", "Servicos financeiros"),
    (("68",), "Imobiliario", "Atividades imobiliarias"),
    (("69", "70", "71", "72", "73", "74"), "Servicos profissionais", "Consultoria e servicos tecnicos"),
    (("85",), "Educacao", "Educacao e treinamento"),
]


DEFAULT_COMPANY_SCORE_RULES = {
    "base_score": 20,
    "status": {
        "active_bonus": 20,
        "inactive_penalty": -15,
    },
    "contact": {
        "email_bonus": 15,
        "phone_bonus": 8,
    },
    "size_bonus": {
        "ME": 8,
        "EPP": 8,
        "MEDIO": 8,
        "GRANDE": 8,
        "DEMAIS": 6,
    },
    "capital_bonus": [
        {"min": 1000000, "bonus": 12, "reason": "capital social alto"},
        {"min": 100000, "bonus": 8, "reason": "capital social relevante"},
        {"min": 10000, "bonus": 4, "reason": "capital social informado"},
    ],
    "age_bonus": [
        {"max_years_exclusive": 2, "bonus": 10, "reason": "empresa nova"},
        {"max_years": 10, "bonus": 6, "reason": "empresa em faixa madura"},
        {"bonus": 3, "reason": "empresa consolidada"},
    ],
    "sector_bonus": {
        "Tecnologia": 7,
        "Saude": 7,
        "Servicos profissionais": 7,
        "Financeiro": 7,
    },
}


def infer_sector(cnae_code, description=""):
    code = "".join(ch for ch in str(cnae_code or "") if ch.isdigit())
    for prefixes, sector, segment in SECTOR_RULES:
        if any(code.startswith(prefix) for prefix in prefixes):
            return sector, segment
    text = (description or "").lower()
    if "software" in text or "tecnologia" in text:
        return "Tecnologia", "Software, dados e servicos digitais"
    if "clinica" in text or "medic" in text:
        return "Saude", "Saude, clinicas e cuidado"
    return "Outros", "Nao classificado"


def parse_date(value):
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def _score_reason(points, label):
    return "%+d %s" % (int(points), label)


def _company_score_rules(rules=None):
    if not rules:
        return DEFAULT_COMPANY_SCORE_RULES
    merged = {
        "base_score": rules.get("base_score", DEFAULT_COMPANY_SCORE_RULES["base_score"]),
        "status": {**DEFAULT_COMPANY_SCORE_RULES["status"], **(rules.get("status") or {})},
        "contact": {**DEFAULT_COMPANY_SCORE_RULES["contact"], **(rules.get("contact") or {})},
        "size_bonus": {**DEFAULT_COMPANY_SCORE_RULES["size_bonus"], **(rules.get("size_bonus") or {})},
        "capital_bonus": rules.get("capital_bonus") or DEFAULT_COMPANY_SCORE_RULES["capital_bonus"],
        "age_bonus": rules.get("age_bonus") or DEFAULT_COMPANY_SCORE_RULES["age_bonus"],
        "sector_bonus": {**DEFAULT_COMPANY_SCORE_RULES["sector_bonus"], **(rules.get("sector_bonus") or {})},
    }
    return merged


def score_company(company, rules=None):
    rules = _company_score_rules(rules)
    score = int(rules.get("base_score", 20) or 0)
    reasons = [_score_reason(score, "base por dado cadastral publico estruturado")]

    status = (company.get("status") or "").lower()
    if "ativa" in status or status == "02":
        bonus = int((rules.get("status") or {}).get("active_bonus", 20) or 0)
        score += bonus
        reasons.append(_score_reason(bonus, "empresa ativa"))
    elif status:
        penalty = int((rules.get("status") or {}).get("inactive_penalty", -15) or 0)
        score += penalty
        reasons.append(_score_reason(penalty, "situacao cadastral nao ativa"))

    if company.get("email"):
        bonus = int((rules.get("contact") or {}).get("email_bonus", 15) or 0)
        score += bonus
        reasons.append(_score_reason(bonus, "possui email publico"))
    else:
        reasons.append("+0 sem email publico")

    if company.get("phone"):
        bonus = int((rules.get("contact") or {}).get("phone_bonus", 8) or 0)
        score += bonus
        reasons.append(_score_reason(bonus, "possui telefone publico"))

    size = (company.get("size") or "").upper()
    size_rules = rules.get("size_bonus") or {}
    if size in ("ME", "EPP", "MEDIO", "GRANDE") and size in size_rules:
        bonus = int(size_rules.get(size) or 0)
        score += bonus
        reasons.append(_score_reason(bonus, "porte com potencial comercial"))
    elif "DEMAIS" in size and "DEMAIS" in size_rules:
        bonus = int(size_rules.get("DEMAIS") or 0)
        score += bonus
        reasons.append(_score_reason(bonus, "porte demais"))

    try:
        capital = float(str(company.get("capital_social") or 0).replace(",", "."))
    except ValueError:
        capital = 0
    for rule in rules.get("capital_bonus") or []:
        if capital >= float(rule.get("min") or 0):
            bonus = int(rule.get("bonus") or 0)
            score += bonus
            reasons.append(_score_reason(bonus, rule.get("reason") or "capital social"))
            break

    opened = parse_date(company.get("opening_date"))
    if opened:
        years = max(0, (datetime.utcnow() - opened).days / 365.25)
        for rule in rules.get("age_bonus") or []:
            applies = False
            if "max_years_exclusive" in rule:
                applies = years < float(rule.get("max_years_exclusive") or 0)
            elif "max_years" in rule:
                applies = years <= float(rule.get("max_years") or 0)
            else:
                applies = True
            if applies:
                bonus = int(rule.get("bonus") or 0)
                score += bonus
                reasons.append(_score_reason(bonus, rule.get("reason") or "idade da empresa"))
                break

    sector, _ = infer_sector(company.get("main_cnae_code"), company.get("main_cnae_description"))
    sector_bonus = int((rules.get("sector_bonus") or {}).get(sector, 0) or 0)
    if sector_bonus:
        score += sector_bonus
        reasons.append(_score_reason(sector_bonus, "setor com boa aderencia B2B"))

    score = max(0, min(100, int(score)))
    return score, reasons


def estimate_market_value(company):
    try:
        capital = float(str(company.get("capital_social") or 0).replace(",", "."))
    except ValueError:
        capital = 0
    size = (company.get("size") or "").upper()
    multiplier = 1.5
    if size in ("ME", "EPP"):
        multiplier = 2.5
    elif size in ("MEDIO", "GRANDE", "DEMAIS"):
        multiplier = 4.0
    return round(max(0, capital * multiplier), 2)
