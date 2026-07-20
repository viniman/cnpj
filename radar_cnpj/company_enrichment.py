import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timedelta
from html.parser import HTMLParser

from .database import now_iso
from .email_hygiene import PERSONAL_DOMAINS, normalize_email


USER_AGENT = "RadarCNPJBot/0.1 (+localhost)"
MAX_HTML_BYTES = 512 * 1024
EMAIL_IN_TEXT_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?:(?:\+|00)?55[\s().-]*)?(?:\(?\d{2}\)?[\s.-]*)?(?:9?\d{4})[\s.-]?\d{4}"
)

SOCIAL_DOMAINS = {
    "linkedin.com": "linkedin",
    "instagram.com": "instagram",
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "tiktok.com": "tiktok",
    "twitter.com": "twitter",
    "x.com": "twitter",
}

ANALYTICS_TECHS = {"google_analytics", "google_tag_manager", "facebook_pixel", "hotjar"}
PLATFORM_TECHS = {"wordpress", "woocommerce", "shopify", "nuvemshop", "wix"}
CHAT_TECHS = {"intercom", "zendesk", "rd_station"}


class SignalParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.scripts = []
        self.meta = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs_map = dict((str(key).lower(), value or "") for key, value in attrs)
        if tag == "a" and attrs_map.get("href"):
            self.links.append(attrs_map["href"])
        if tag == "script" and attrs_map.get("src"):
            self.scripts.append(attrs_map["src"])
        if tag == "meta":
            self.meta.append(attrs_map)

    def handle_data(self, data):
        if data and data.strip():
            self.text.append(data.strip())


def unique(values):
    seen = set()
    items = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


def normalize_url(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urllib.parse.urlparse(raw)
    if not parsed.netloc:
        return raw
    path = parsed.path or "/"
    return urllib.parse.urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            parsed.query,
            "",
        )
    )


def domain_from_url(value):
    parsed = urllib.parse.urlparse(normalize_url(value))
    host = (parsed.netloc or "").split("@")[-1].split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def parse_html_signals(html_text):
    parser = SignalParser()
    try:
        parser.feed(html_text or "")
    except Exception:
        pass
    text = " ".join(parser.text)
    return {
        "links": parser.links,
        "scripts": parser.scripts,
        "meta": parser.meta,
        "text": text,
        "combined": "\n".join([html_text or "", text, "\n".join(parser.links), "\n".join(parser.scripts)]),
    }


def extract_emails(html_text):
    decoded = html.unescape(html_text or "").replace("%40", "@")
    results = []
    for match in EMAIL_IN_TEXT_RE.findall(decoded):
        email = normalize_email(match).strip(".,;:")
        if email:
            results.append(email)
    return sorted(unique(results))


def normalize_phone(value):
    digits = re.sub(r"\D+", "", value or "")
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]
    if len(digits) in (10, 11):
        return digits
    return ""


def extract_phones(html_text):
    decoded = html.unescape(html_text or "")
    phones = [normalize_phone(match) for match in PHONE_RE.findall(decoded)]
    return sorted(unique(phone for phone in phones if phone))


def extract_social_links(html_text, base_url=""):
    signals = parse_html_signals(html_text)
    links = []
    for href in signals["links"]:
        url = urllib.parse.urljoin(base_url or "", href)
        domain = domain_from_url(url)
        if any(domain == item or domain.endswith("." + item) for item in SOCIAL_DOMAINS):
            links.append(url.split("#", 1)[0])
    return sorted(unique(links))


def detect_technologies(headers=None, html_text=""):
    headers = headers or {}
    header_text = "\n".join("%s: %s" % (key, value) for key, value in headers.items()).lower()
    body = (html_text or "").lower()
    techs = set()

    checks = [
        ("wordpress", ["wp-content", "wp-includes", "generator\" content=\"wordpress"]),
        ("woocommerce", ["woocommerce", "wc-cart-fragments"]),
        ("shopify", ["cdn.shopify.com", "x-shopify", "shopify.theme"]),
        ("nuvemshop", ["nuvemshop", "tiendanube"]),
        ("wix", ["wixstatic", "wix.com"]),
        ("google_analytics", ["google-analytics.com", "gtag/js", "ga('create'", "gtag("]),
        ("google_tag_manager", ["googletagmanager.com/gtm.js", "gtm-"]),
        ("facebook_pixel", ["connect.facebook.net", "fbq("]),
        ("rd_station", ["rdstation", "resultadosdigitais"]),
        ("hotjar", ["hotjar.com", "hj("]),
        ("intercom", ["intercom.io", "intercomsettings"]),
        ("zendesk", ["zendesk.com", "zdassets.com"]),
    ]
    combined = body + "\n" + header_text
    for tech, needles in checks:
        if any(needle in combined for needle in needles):
            techs.add(tech)
    if "server: cloudflare" in header_text or "cf-cache-status" in header_text:
        techs.add("cloudflare")
    return sorted(techs)


def digital_maturity(source_url="", emails=None, phones=None, social_links=None, technologies=None):
    emails = emails or []
    phones = phones or []
    social_links = social_links or []
    technologies = set(technologies or [])
    score = 0
    reasons = []

    if source_url and domain_from_url(source_url):
        score += 15
        reasons.append("Site informado")
    else:
        score -= 5
        reasons.append("Fonte sem URL real")

    if emails:
        score += 20
        reasons.append("E-mail publicado no site")
        if any((email.split("@", 1)[1] if "@" in email else "") not in PERSONAL_DOMAINS for email in emails):
            reasons.append("E-mail corporativo publicado")
    else:
        score -= 10
        reasons.append("Nenhum e-mail publicado encontrado")

    if phones:
        score += 10
        reasons.append("Telefone ou WhatsApp publicado")

    if social_links:
        score += 15
        reasons.append("Link social institucional encontrado")

    if technologies & ANALYTICS_TECHS:
        score += 15
        reasons.append("Analytics ou tag manager detectado")

    if technologies & PLATFORM_TECHS:
        score += 15
        reasons.append("CMS ou e-commerce detectado")

    if technologies & CHAT_TECHS:
        score += 10
        reasons.append("Ferramenta de atendimento ou automacao detectada")

    if not technologies:
        score -= 10
        reasons.append("Nenhuma tecnologia detectada")

    score = max(0, min(100, int(score)))
    if score >= 70:
        confidence = "high"
    elif score >= 35:
        confidence = "medium"
    else:
        confidence = "low"
    return score, reasons, confidence


def enrich_from_html(company=None, source_url="", html_text="", headers=None, source_type="provided_html"):
    company = company or {}
    source_url = source_url or company.get("source_url") or ""
    headers = headers or {}
    emails = extract_emails(html_text)
    phones = extract_phones(html_text)
    social_links = extract_social_links(html_text, base_url=source_url)
    technologies = detect_technologies(headers, html_text)
    score, reasons, confidence = digital_maturity(source_url, emails, phones, social_links, technologies)
    return {
        "company_id": company.get("id"),
        "company_name": company.get("trade_name") or company.get("legal_name") or "",
        "source_url": normalize_url(source_url) if source_url else "",
        "source_type": source_type,
        "detected_domain": domain_from_url(source_url),
        "emails": emails,
        "phones": phones,
        "social_links": social_links,
        "technologies": technologies,
        "digital_maturity_score": score,
        "reasons": reasons,
        "confidence": confidence,
        "collected_at": now_iso(),
    }


def robots_allowed(url, user_agent=USER_AGENT, timeout=5):
    normalized = normalize_url(url)
    parsed = urllib.parse.urlparse(normalized)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False, "URL invalida para consulta publica"
    robots_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": user_agent})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(128 * 1024).decode("utf-8", errors="replace")
        parser.parse(raw.splitlines())
        return parser.can_fetch(user_agent, normalized), "robots.txt consultado"
    except Exception:
        return True, "robots.txt indisponivel; seguindo com uma requisicao conservadora"


def fetch_url(url, timeout=10, max_bytes=MAX_HTML_BYTES, user_agent=USER_AGENT):
    normalized = normalize_url(url)
    request = urllib.request.Request(
        normalized,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            body = body[:max_bytes]
        content_type = response.headers.get("Content-Type", "")
        encoding = response.headers.get_content_charset() or "utf-8"
        text = body.decode(encoding, errors="replace")
        headers = dict((key, value) for key, value in response.headers.items())
        headers["Content-Type"] = content_type
        return {
            "url": normalized,
            "status_code": getattr(response, "status", 200),
            "headers": headers,
            "body_text": text,
            "body_hash": hashlib.sha256(body).hexdigest(),
        }


def cache_lookup(conn, url):
    normalized = normalize_url(url)
    row = conn.execute(
        "SELECT * FROM scraping_cache WHERE url = ? AND expires_at > ?",
        (normalized, now_iso()),
    ).fetchone()
    return dict(row) if row else None


def cache_store(conn, fetched, ttl_days=30):
    timestamp = now_iso()
    url = normalize_url(fetched.get("url") or "")
    expires_at = (datetime.utcnow() + timedelta(days=int(ttl_days or 30))).replace(microsecond=0).isoformat() + "Z"
    conn.execute(
        """
        INSERT INTO scraping_cache (url, status_code, headers_json, body_hash, body_text, fetched_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            status_code = excluded.status_code,
            headers_json = excluded.headers_json,
            body_hash = excluded.body_hash,
            body_text = excluded.body_text,
            fetched_at = excluded.fetched_at,
            expires_at = excluded.expires_at
        """,
        (
            url,
            int(fetched.get("status_code") or 0),
            json.dumps(fetched.get("headers") or {}, ensure_ascii=True),
            fetched.get("body_hash") or "",
            fetched.get("body_text") or "",
            timestamp,
            expires_at,
        ),
    )


def parsed_enrichment_row(row):
    if not row:
        return None
    data = dict(row)
    data["emails"] = json.loads(data.pop("emails_json") or "[]")
    data["phones"] = json.loads(data.pop("phones_json") or "[]")
    data["social_links"] = json.loads(data.pop("social_links_json") or "[]")
    data["technologies"] = json.loads(data.pop("technologies_json") or "[]")
    data["reasons"] = json.loads(data.pop("reasons_json") or "[]")
    return data
