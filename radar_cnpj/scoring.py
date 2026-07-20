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


def score_company(company):
    score = 20
    reasons = ["+20 base por dado cadastral publico estruturado"]

    status = (company.get("status") or "").lower()
    if "ativa" in status or status == "02":
        score += 20
        reasons.append("+20 empresa ativa")
    elif status:
        score -= 15
        reasons.append("-15 situacao cadastral nao ativa")

    if company.get("email"):
        score += 15
        reasons.append("+15 possui email publico")
    else:
        reasons.append("+0 sem email publico")

    if company.get("phone"):
        score += 8
        reasons.append("+8 possui telefone publico")

    size = (company.get("size") or "").upper()
    if size in ("ME", "EPP", "MEDIO", "GRANDE"):
        score += 8
        reasons.append("+8 porte com potencial comercial")
    elif "DEMAIS" in size:
        score += 6
        reasons.append("+6 porte demais")

    try:
        capital = float(str(company.get("capital_social") or 0).replace(",", "."))
    except ValueError:
        capital = 0
    if capital >= 1000000:
        score += 12
        reasons.append("+12 capital social alto")
    elif capital >= 100000:
        score += 8
        reasons.append("+8 capital social relevante")
    elif capital >= 10000:
        score += 4
        reasons.append("+4 capital social informado")

    opened = parse_date(company.get("opening_date"))
    if opened:
        years = max(0, (datetime.utcnow() - opened).days / 365.25)
        if years < 2:
            score += 10
            reasons.append("+10 empresa nova")
        elif years <= 10:
            score += 6
            reasons.append("+6 empresa em faixa madura")
        else:
            score += 3
            reasons.append("+3 empresa consolidada")

    sector, _ = infer_sector(company.get("main_cnae_code"), company.get("main_cnae_description"))
    if sector in ("Tecnologia", "Saude", "Servicos profissionais", "Financeiro"):
        score += 7
        reasons.append("+7 setor com boa aderencia B2B")

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

