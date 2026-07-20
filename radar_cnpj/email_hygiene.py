import re


EMAIL_RE = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.IGNORECASE)

GENERIC_PREFIXES = {
    "contato",
    "comercial",
    "vendas",
    "financeiro",
    "administrativo",
    "admin",
    "atendimento",
    "sac",
    "rh",
    "marketing",
    "info",
}

PERSONAL_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "yahoo.com",
    "icloud.com",
    "live.com",
    "bol.com.br",
    "uol.com.br",
}

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "yopmail.com",
}


def normalize_email(email):
    return (email or "").strip().lower()


def classify_email(email, suppression_set=None, opt_out_set=None, seen=None):
    suppression_set = suppression_set or set()
    opt_out_set = opt_out_set or set()
    seen = seen if seen is not None else set()
    normalized = normalize_email(email)

    labels = []
    reasons = []
    score = 100

    if not normalized or not EMAIL_RE.match(normalized):
        return {
            "email": normalized,
            "classification": "Invalido",
            "labels": ["Invalido"],
            "score": 0,
            "reasons": ["Formato de email invalido"],
        }

    local, domain = normalized.split("@", 1)

    if normalized in seen:
        labels.append("Duplicado")
        reasons.append("Email duplicado nesta validacao")
        score -= 35
    seen.add(normalized)

    if normalized in suppression_set:
        labels.append("Suprimido")
        reasons.append("Email presente na lista de supressao")
        score = min(score, 5)

    if normalized in opt_out_set:
        labels.append("Opt-out")
        reasons.append("Contato solicitou opt-out")
        score = min(score, 0)

    if domain in DISPOSABLE_DOMAINS:
        labels.append("Suspeito")
        reasons.append("Dominio descartavel")
        score -= 50

    if local in GENERIC_PREFIXES:
        labels.append("Generico")
        reasons.append("Caixa generica da empresa")
        score -= 10

    if domain in PERSONAL_DOMAINS:
        labels.append("Pessoal")
        reasons.append("Dominio de email pessoal")
        score -= 20
    else:
        labels.append("Corporativo")
        reasons.append("Dominio aparenta ser corporativo")
        score += 5

    score = max(0, min(100, score))
    if "Opt-out" in labels:
        primary = "Opt-out"
    elif "Suprimido" in labels:
        primary = "Suprimido"
    elif "Suspeito" in labels:
        primary = "Suspeito"
    elif "Duplicado" in labels:
        primary = "Duplicado"
    elif "Generico" in labels:
        primary = "Generico"
    elif "Pessoal" in labels:
        primary = "Pessoal"
    else:
        primary = "Valido"

    return {
        "email": normalized,
        "classification": primary,
        "labels": labels,
        "score": score,
        "reasons": reasons,
    }

