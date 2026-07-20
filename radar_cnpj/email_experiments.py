import re
import unicodedata
import urllib.parse


CAMPAIGN_MODE = "simulated"
PROVIDER = "simulated"

BLOCKING_HYGIENE = {"Invalido", "Suprimido", "Opt-out", "Suspeito", "Pessoal"}
BLOCKING_SCORE_LABELS = {
    "disposable",
    "suppressed",
    "invalid",
    "personal_domain",
    "shared_contact",
    "shared_domain",
    "known_shared_domain",
}

EVENT_STATUS = {
    "planned": "planned",
    "sent": "simulated_sent",
    "delivered": "delivered",
    "clicked": "clicked",
    "replied": "replied",
    "converted": "converted",
    "bounce": "bounced",
    "complaint": "complained",
    "blocked": "blocked",
}

FUNNEL_EVENTS = ["sent", "delivered", "clicked", "replied", "converted", "bounce", "complaint", "blocked"]


def ascii_slug(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "campaign"


def append_utm(url, campaign_name, variant_name, niche):
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query.update(
        {
            "utm_campaign": ascii_slug(campaign_name),
            "utm_content": ascii_slug(variant_name),
            "utm_source": ascii_slug(niche),
            "utm_medium": "email_simulated",
        }
    )
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))


def email_eligibility(email, hygiene, scoring):
    if not email:
        return False, "Lead sem e-mail"
    if hygiene.get("classification") in BLOCKING_HYGIENE:
        return False, "Higiene bloqueou e-mail: %s" % hygiene.get("classification")
    labels = set(scoring.get("labels") or [])
    blocked_labels = sorted(labels & BLOCKING_SCORE_LABELS)
    if blocked_labels:
        return False, "Score bloqueou labels: %s" % ", ".join(blocked_labels)
    if int(scoring.get("score") or 0) < 30:
        return False, "Score de e-mail abaixo do minimo: %s" % scoring.get("score")
    return True, ""


def lead_score(company_score, email_score):
    company_score = int(company_score or 0)
    email_score = int(email_score or 0)
    if not email_score:
        return company_score
    return int(round((company_score * 0.45) + (email_score * 0.55)))


def empty_funnel():
    data = {"planned": 0}
    for event_type in FUNNEL_EVENTS:
        data[event_type] = 0
    return data

