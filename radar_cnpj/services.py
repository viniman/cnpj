import csv
import io
import json
import os
import re
import unicodedata
from datetime import datetime, timedelta

from .company_enrichment import (
    cache_lookup,
    cache_store,
    enrich_from_html,
    fetch_url,
    normalize_url,
    parsed_enrichment_row,
    robots_allowed,
)
from .database import now_iso
from .email_experiments import (
    CAMPAIGN_MODE,
    EVENT_STATUS,
    PROVIDER,
    append_utm,
    email_eligibility,
    empty_funnel,
    lead_score,
)
from .email_hygiene import classify_email, normalize_email
from .email_scoring import score_email
from .email_templates import (
    COMPLIANCE_FOOTER_TEMPLATE,
    SUPPORTED_VARIABLES,
    build_company_template_context,
    extract_variables,
    render_template,
    validate_editable_template,
)
from .exporter import rows_to_csv_bytes, rows_to_xlsx_bytes
from .receita_importer import parse_receita_directory, parse_receita_zip_directory
from .scoring import estimate_market_value, infer_sector, score_company


ORG_ID = 1
USER_ID = 1


def dict_row(row):
    return dict(row) if row is not None else None


def only_digits(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def format_cnpj(value):
    digits = only_digits(value)
    if len(digits) != 14:
        return str(value or "").strip()
    return "%s.%s.%s/%s-%s" % (
        digits[:2],
        digits[2:5],
        digits[5:8],
        digits[8:12],
        digits[12:],
    )


def is_valid_cnpj(value):
    digits = only_digits(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False

    def digit(numbers, weights):
        total = sum(int(n) * w for n, w in zip(numbers, weights))
        mod = total % 11
        return "0" if mod < 2 else str(11 - mod)

    d1 = digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = digit(digits[:12] + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return digits[-2:] == d1 + d2


def audit(conn, action, entity_type, entity_id=None, metadata=None):
    conn.execute(
        """
        INSERT INTO audit_logs (org_id, user_id, action, entity_type, entity_id, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            USER_ID,
            action,
            entity_type,
            str(entity_id) if entity_id is not None else None,
            json.dumps(metadata or {}, ensure_ascii=True),
            now_iso(),
        ),
    )


def upsert_company(conn, payload, source_name="Importacao local", source_url="", legal_basis="Legitimo interesse B2B"):
    cnpj = format_cnpj(payload.get("cnpj"))
    digits = only_digits(cnpj)
    if len(digits) != 14:
        raise ValueError("CNPJ invalido ou incompleto: %s" % payload.get("cnpj"))

    payload = dict(payload)
    payload["cnpj"] = cnpj
    payload["cnpj_root"] = digits[:8]
    payload["source_name"] = payload.get("source_name") or source_name
    payload["source_url"] = payload.get("source_url") or source_url
    payload["legal_basis"] = payload.get("legal_basis") or legal_basis
    payload["collected_at"] = payload.get("collected_at") or now_iso()
    payload["updated_at"] = now_iso()

    sector, segment = infer_sector(payload.get("main_cnae_code"), payload.get("main_cnae_description"))
    payload["sector"] = payload.get("sector") or sector
    payload["segment"] = payload.get("segment") or segment
    payload["opportunity_score"], reasons = score_company(payload)
    payload["score_reasons"] = json.dumps(reasons, ensure_ascii=True)
    payload["market_value_estimate"] = estimate_market_value(payload)

    fields = [
        "cnpj",
        "cnpj_root",
        "legal_name",
        "trade_name",
        "status",
        "opening_date",
        "status_date",
        "main_cnae_code",
        "main_cnae_description",
        "secondary_cnaes",
        "legal_nature",
        "size",
        "establishment_type",
        "street_type",
        "street",
        "number",
        "complement",
        "district",
        "city",
        "state",
        "zip_code",
        "email",
        "phone",
        "capital_social",
        "sector",
        "segment",
        "market_value_estimate",
        "opportunity_score",
        "score_reasons",
        "source_name",
        "source_url",
        "collected_at",
        "legal_basis",
        "updated_at",
    ]
    defaults = {
        "legal_name": payload.get("trade_name") or cnpj,
        "capital_social": 0,
        "source_name": source_name,
        "legal_basis": legal_basis,
    }
    values = [payload.get(field, defaults.get(field, "")) for field in fields]
    placeholders = ", ".join(["?"] * len(fields))
    updates = ", ".join("%s = excluded.%s" % (field, field) for field in fields if field != "cnpj")
    sql = """
        INSERT INTO companies (%s) VALUES (%s)
        ON CONFLICT(cnpj) DO UPDATE SET %s
    """ % (
        ", ".join(fields),
        placeholders,
        updates,
    )
    conn.execute(sql, values)
    company = conn.execute("SELECT id FROM companies WHERE cnpj = ?", (cnpj,)).fetchone()
    company_id = company["id"]

    if payload.get("main_cnae_code"):
        conn.execute(
            """
            INSERT INTO cnaes (code, description, sector)
            VALUES (?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET description = excluded.description, sector = excluded.sector
            """,
            (payload.get("main_cnae_code"), payload.get("main_cnae_description") or "", payload["sector"]),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO company_cnaes (company_id, cnae_code, is_primary)
            VALUES (?, ?, 1)
            """,
            (company_id, payload.get("main_cnae_code")),
        )

    partners = payload.get("partners") or []
    if isinstance(partners, str):
        partners = parse_partner_string(partners)
    if partners:
        conn.execute("DELETE FROM partners WHERE company_id = ?", (company_id,))
        for partner in partners:
            if not partner.get("name"):
                continue
            conn.execute(
                """
                INSERT INTO partners (company_id, name, qualification, entry_date, age_range, document_masked)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id,
                    partner.get("name"),
                    partner.get("qualification", ""),
                    partner.get("entry_date", ""),
                    partner.get("age_range", ""),
                    partner.get("document_masked", ""),
                ),
            )

    return company_id


def parse_partner_string(value):
    partners = []
    for chunk in str(value or "").split(";"):
        parts = [part.strip() for part in chunk.split("|")]
        if not parts or not parts[0]:
            continue
        partners.append(
            {
                "name": parts[0],
                "qualification": parts[1] if len(parts) > 1 else "",
                "entry_date": parts[2] if len(parts) > 2 else "",
            }
        )
    return partners


HEADER_MAP = {
    "cnpj": "cnpj",
    "razao_social": "legal_name",
    "razao social": "legal_name",
    "legal_name": "legal_name",
    "nome_fantasia": "trade_name",
    "nome fantasia": "trade_name",
    "trade_name": "trade_name",
    "situacao": "status",
    "situacao_cadastral": "status",
    "status": "status",
    "data_abertura": "opening_date",
    "opening_date": "opening_date",
    "cnae": "main_cnae_code",
    "cnae_principal": "main_cnae_code",
    "main_cnae_code": "main_cnae_code",
    "descricao_cnae": "main_cnae_description",
    "main_cnae_description": "main_cnae_description",
    "cnaes_secundarios": "secondary_cnaes",
    "natureza_juridica": "legal_nature",
    "legal_nature": "legal_nature",
    "porte": "size",
    "size": "size",
    "tipo": "establishment_type",
    "logradouro": "street",
    "street": "street",
    "numero": "number",
    "number": "number",
    "complemento": "complement",
    "bairro": "district",
    "cidade": "city",
    "city": "city",
    "uf": "state",
    "estado": "state",
    "state": "state",
    "cep": "zip_code",
    "email": "email",
    "telefone": "phone",
    "phone": "phone",
    "capital_social": "capital_social",
    "socios": "partners",
    "partners": "partners",
    "source_name": "source_name",
    "source_url": "source_url",
    "legal_basis": "legal_basis",
}


def normalize_header(header):
    return re.sub(r"\s+", " ", str(header or "").strip().lower())


def import_simplified_csv(conn, path, source_name, source_url="", legal_basis="Legitimo interesse B2B", limit=None):
    with open(path, "rb") as raw:
        sample = raw.read(4096)
    text_sample = sample.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text_sample, delimiters=",;|\t")
    except csv.Error:
        dialect = csv.excel

    imported = 0
    errors = 0
    with open(path, "r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        for row in reader:
            if limit and imported >= int(limit):
                break
            payload = {}
            for header, value in row.items():
                key = HEADER_MAP.get(normalize_header(header))
                if key:
                    payload[key] = (value or "").strip()
            try:
                upsert_company(conn, payload, source_name, source_url, legal_basis)
                imported += 1
            except Exception:
                errors += 1
    return imported, errors


def import_source(conn, path, source_name, source_url="", legal_basis="Legitimo interesse B2B", limit=1000):
    started = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO import_jobs (source_name, source_path, source_url, status, started_at, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (source_name, path, source_url, "running", started, "Importacao iniciada"),
    )
    job_id = cursor.lastrowid
    imported = 0
    errors = 0
    try:
        if os.path.isdir(path):
            payloads = parse_receita_directory(path, limit=limit)
            for payload in payloads:
                try:
                    upsert_company(conn, payload, source_name, source_url, legal_basis)
                    imported += 1
                except Exception:
                    errors += 1
        else:
            imported, errors = import_simplified_csv(conn, path, source_name, source_url, legal_basis, limit)
        status = "completed"
        message = "Importadas %s empresas com %s erros" % (imported, errors)
    except Exception as exc:
        status = "failed"
        message = str(exc)
    conn.execute(
        """
        UPDATE import_jobs
        SET status = ?, total_rows = ?, imported_rows = ?, error_rows = ?, message = ?, finished_at = ?
        WHERE id = ?
        """,
        (status, imported + errors, imported, errors, message, now_iso(), job_id),
    )
    audit(conn, "import_source", "import_job", job_id, {"path": path, "imported": imported, "errors": errors})
    return {"id": job_id, "status": status, "imported_rows": imported, "error_rows": errors, "message": message}


def import_official_zip_directory(
    conn,
    path,
    source_name,
    source_url="",
    legal_basis="Legitimo interesse B2B",
    chunk=1,
    limit=1000,
):
    started = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO import_jobs (source_name, source_path, source_url, status, started_at, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (source_name, path, source_url, "running", started, "Importacao oficial iniciada"),
    )
    job_id = cursor.lastrowid
    imported = 0
    errors = 0
    try:
        payloads = parse_receita_zip_directory(path, chunk=chunk, limit=limit)
        for payload in payloads:
            try:
                upsert_company(conn, payload, source_name, source_url, legal_basis)
                imported += 1
            except Exception:
                errors += 1
        status = "completed"
        message = "Importadas %s empresas oficiais com %s erros" % (imported, errors)
    except Exception as exc:
        status = "failed"
        message = str(exc)
    conn.execute(
        """
        UPDATE import_jobs
        SET status = ?, total_rows = ?, imported_rows = ?, error_rows = ?, message = ?, finished_at = ?
        WHERE id = ?
        """,
        (status, imported + errors, imported, errors, message, now_iso(), job_id),
    )
    audit(
        conn,
        "import_official_zip_directory",
        "import_job",
        job_id,
        {"path": path, "chunk": chunk, "limit": limit, "imported": imported, "errors": errors},
    )
    return {"id": job_id, "status": status, "imported_rows": imported, "error_rows": errors, "message": message}


def seed_sample(conn):
    sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "samples", "companies.csv"))
    return import_source(
        conn,
        sample_path,
        "Amostra interna ficticia",
        "data/samples/companies.csv",
        "Legitimo interesse B2B para avaliacao interna",
        limit=1000,
    )


def search_companies(conn, params):
    limit = min(int(params.get("limit", 50) or 50), 200)
    offset = max(int(params.get("offset", 0) or 0), 0)
    where = []
    values = []

    query = (params.get("query") or "").strip()
    if query:
        like = "%%%s%%" % query.lower()
        where.append(
            "(lower(legal_name) LIKE ? OR lower(trade_name) LIKE ? OR cnpj LIKE ? OR lower(email) LIKE ? OR lower(city) LIKE ?)"
        )
        values.extend([like, like, "%%%s%%" % query, like, like])

    for key, column in [
        ("state", "state"),
        ("city", "city"),
        ("cnae", "main_cnae_code"),
        ("status", "status"),
        ("size", "size"),
        ("sector", "sector"),
    ]:
        value = (params.get(key) or "").strip()
        if value:
            where.append("lower(%s) LIKE ?" % column)
            values.append("%%%s%%" % value.lower())

    if str(params.get("has_email", "")).lower() in ("1", "true", "yes", "sim"):
        where.append("email IS NOT NULL AND email != ''")
    if str(params.get("has_phone", "")).lower() in ("1", "true", "yes", "sim"):
        where.append("phone IS NOT NULL AND phone != ''")

    min_score = params.get("min_score")
    if min_score:
        where.append("opportunity_score >= ?")
        values.append(int(min_score))

    sql_where = "WHERE " + " AND ".join(where) if where else ""
    total = conn.execute("SELECT COUNT(*) AS total FROM companies %s" % sql_where, values).fetchone()["total"]
    rows = conn.execute(
        """
        SELECT id, cnpj, legal_name, trade_name, status, city, state, main_cnae_code,
               main_cnae_description, size, email, phone, sector, opportunity_score,
               source_name, collected_at
        FROM companies
        %s
        ORDER BY opportunity_score DESC, legal_name ASC
        LIMIT ? OFFSET ?
        """
        % sql_where,
        values + [limit, offset],
    ).fetchall()
    return {"total": total, "limit": limit, "offset": offset, "items": [dict_row(row) for row in rows]}


def get_company(conn, company_id):
    company = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    if not company:
        return None
    data = dict_row(company)
    data["score_reasons"] = json.loads(data.get("score_reasons") or "[]")
    data["partners"] = [
        dict_row(row)
        for row in conn.execute(
            "SELECT name, qualification, entry_date, age_range, document_masked FROM partners WHERE company_id = ? ORDER BY name",
            (company_id,),
        ).fetchall()
    ]
    return data


def get_company_enrichment(conn, company_id):
    row = conn.execute(
        """
        SELECT ce.*, c.legal_name, c.trade_name, c.cnpj
        FROM company_enrichment ce
        JOIN companies c ON c.id = ce.company_id
        WHERE ce.company_id = ?
        """,
        (company_id,),
    ).fetchone()
    return parsed_enrichment_row(row)


def persist_company_enrichment(conn, company_id, enrichment):
    timestamp = now_iso()
    collected_at = enrichment.get("collected_at") or timestamp
    conn.execute(
        """
        INSERT INTO company_enrichment (
            company_id, source_url, source_type, detected_domain, emails_json,
            phones_json, social_links_json, technologies_json,
            digital_maturity_score, reasons_json, confidence, collected_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(company_id) DO UPDATE SET
            source_url = excluded.source_url,
            source_type = excluded.source_type,
            detected_domain = excluded.detected_domain,
            emails_json = excluded.emails_json,
            phones_json = excluded.phones_json,
            social_links_json = excluded.social_links_json,
            technologies_json = excluded.technologies_json,
            digital_maturity_score = excluded.digital_maturity_score,
            reasons_json = excluded.reasons_json,
            confidence = excluded.confidence,
            collected_at = excluded.collected_at,
            updated_at = excluded.updated_at
        """,
        (
            company_id,
            enrichment.get("source_url") or "",
            enrichment.get("source_type") or "manual",
            enrichment.get("detected_domain") or "",
            json.dumps(enrichment.get("emails") or [], ensure_ascii=True),
            json.dumps(enrichment.get("phones") or [], ensure_ascii=True),
            json.dumps(enrichment.get("social_links") or [], ensure_ascii=True),
            json.dumps(enrichment.get("technologies") or [], ensure_ascii=True),
            int(enrichment.get("digital_maturity_score") or 0),
            json.dumps(enrichment.get("reasons") or [], ensure_ascii=True),
            enrichment.get("confidence") or "low",
            collected_at,
            timestamp,
        ),
    )
    audit(
        conn,
        "enrich_company",
        "company",
        company_id,
        {
            "source_url": enrichment.get("source_url"),
            "source_type": enrichment.get("source_type"),
            "score": enrichment.get("digital_maturity_score"),
        },
    )
    return get_company_enrichment(conn, company_id)


def start_scraping_job(conn, company_id, url, status="running", message=""):
    cursor = conn.execute(
        """
        INSERT INTO scraping_jobs (company_id, url, status, message, started_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (company_id, url, status, message, now_iso()),
    )
    return cursor.lastrowid


def finish_scraping_job(conn, job_id, status, message):
    conn.execute(
        """
        UPDATE scraping_jobs
        SET status = ?, message = ?, finished_at = ?
        WHERE id = ?
        """,
        (status, message, now_iso(), job_id),
    )


def enrich_company(conn, company_id, url="", html="", source_url="", ttl_days=30):
    company = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    if not company:
        raise ValueError("Empresa nao encontrada")

    company_data = dict_row(company)
    source_url = source_url or url or ""
    if html:
        enrichment = enrich_from_html(
            company_data,
            source_url=source_url,
            html_text=html,
            headers={},
            source_type="provided_html",
        )
        saved = persist_company_enrichment(conn, company_id, enrichment)
        saved["job"] = {"status": "completed", "message": "HTML informado processado localmente"}
        return saved

    if not url:
        raise ValueError("Informe html ou url para enriquecer a empresa")

    normalized_url = normalize_url(url)
    job_id = start_scraping_job(conn, company_id, normalized_url, "running", "Coleta iniciada")
    try:
        cached = cache_lookup(conn, normalized_url)
        if cached:
            headers = json.loads(cached["headers_json"] or "{}")
            enrichment = enrich_from_html(
                company_data,
                source_url=normalized_url,
                html_text=cached["body_text"],
                headers=headers,
                source_type="public_website",
            )
            message = "Cache reutilizado dentro do TTL"
        else:
            allowed, robots_message = robots_allowed(normalized_url)
            if not allowed:
                finish_scraping_job(conn, job_id, "blocked_by_robots", robots_message)
                raise ValueError("Busca bloqueada por robots.txt")
            fetched = fetch_url(normalized_url)
            cache_store(conn, fetched, ttl_days=ttl_days)
            enrichment = enrich_from_html(
                company_data,
                source_url=normalized_url,
                html_text=fetched["body_text"],
                headers=fetched["headers"],
                source_type="public_website",
            )
            message = "URL coletada; %s" % robots_message
        saved = persist_company_enrichment(conn, company_id, enrichment)
        finish_scraping_job(conn, job_id, "completed", message)
        saved["job"] = {"id": job_id, "status": "completed", "message": message}
        return saved
    except Exception as exc:
        existing = conn.execute("SELECT status FROM scraping_jobs WHERE id = ?", (job_id,)).fetchone()
        if existing and existing["status"] == "running":
            finish_scraping_job(conn, job_id, "failed", str(exc))
        raise


def dashboard(conn):
    totals = conn.execute(
        """
        SELECT
            COUNT(*) AS companies,
            SUM(CASE WHEN lower(status) LIKE '%ativa%' THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END) AS with_email,
            SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) AS with_phone,
            ROUND(AVG(opportunity_score), 1) AS avg_score
        FROM companies
        """
    ).fetchone()
    lists = conn.execute("SELECT COUNT(*) AS total FROM lists WHERE org_id = ?", (ORG_ID,)).fetchone()["total"]
    top_states = conn.execute(
        "SELECT state, COUNT(*) AS total FROM companies WHERE state != '' GROUP BY state ORDER BY total DESC LIMIT 8"
    ).fetchall()
    top_cnaes = conn.execute(
        """
        SELECT main_cnae_code AS code, main_cnae_description AS description, COUNT(*) AS total
        FROM companies
        WHERE main_cnae_code != ''
        GROUP BY main_cnae_code, main_cnae_description
        ORDER BY total DESC
        LIMIT 8
        """
    ).fetchall()
    imports = conn.execute(
        "SELECT * FROM import_jobs ORDER BY id DESC LIMIT 5"
    ).fetchall()
    return {
        "totals": dict_row(totals),
        "lists": lists,
        "top_states": [dict_row(row) for row in top_states],
        "top_cnaes": [dict_row(row) for row in top_cnaes],
        "imports": [dict_row(row) for row in imports],
    }


def create_list(conn, name, description=""):
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO lists (org_id, name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ORG_ID, name, description, timestamp, timestamp),
    )
    list_id = cursor.lastrowid
    audit(conn, "create_list", "list", list_id, {"name": name})
    return get_list(conn, list_id)


def list_lists(conn):
    rows = conn.execute(
        """
        SELECT l.*, COUNT(lc.company_id) AS company_count,
               SUM(CASE WHEN c.email IS NOT NULL AND c.email != '' THEN 1 ELSE 0 END) AS email_count,
               ROUND(AVG(c.opportunity_score), 1) AS avg_score
        FROM lists l
        LEFT JOIN list_companies lc ON lc.list_id = l.id
        LEFT JOIN companies c ON c.id = lc.company_id
        WHERE l.org_id = ?
        GROUP BY l.id
        ORDER BY l.updated_at DESC
        """,
        (ORG_ID,),
    ).fetchall()
    return [dict_row(row) for row in rows]


def get_list(conn, list_id):
    base = conn.execute("SELECT * FROM lists WHERE id = ? AND org_id = ?", (list_id, ORG_ID)).fetchone()
    if not base:
        return None
    companies = conn.execute(
        """
        SELECT c.id, c.cnpj, c.legal_name, c.trade_name, c.status, c.city, c.state,
               c.main_cnae_code, c.size, c.email, c.phone, c.sector, c.opportunity_score,
               lc.status AS list_status, lc.notes
        FROM list_companies lc
        JOIN companies c ON c.id = lc.company_id
        WHERE lc.list_id = ?
        ORDER BY c.opportunity_score DESC, c.legal_name ASC
        """,
        (list_id,),
    ).fetchall()
    stats = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN c.email IS NOT NULL AND c.email != '' THEN 1 ELSE 0 END) AS with_email,
               SUM(CASE WHEN c.phone IS NOT NULL AND c.phone != '' THEN 1 ELSE 0 END) AS with_phone,
               ROUND(AVG(c.opportunity_score), 1) AS avg_score
        FROM list_companies lc
        JOIN companies c ON c.id = lc.company_id
        WHERE lc.list_id = ?
        """,
        (list_id,),
    ).fetchone()
    data = dict_row(base)
    data["stats"] = dict_row(stats)
    data["companies"] = [dict_row(row) for row in companies]
    return data


def add_companies_to_list(conn, list_id, company_ids):
    timestamp = now_iso()
    added = 0
    for company_id in company_ids:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO list_companies (list_id, company_id, created_at)
            VALUES (?, ?, ?)
            """,
            (list_id, int(company_id), timestamp),
        )
        added += cursor.rowcount
    conn.execute("UPDATE lists SET updated_at = ? WHERE id = ?", (timestamp, list_id))
    audit(conn, "add_companies_to_list", "list", list_id, {"company_ids": company_ids, "added": added})
    return {"added": added, "list": get_list(conn, list_id)}


def remove_company_from_list(conn, list_id, company_id):
    conn.execute("DELETE FROM list_companies WHERE list_id = ? AND company_id = ?", (list_id, company_id))
    conn.execute("UPDATE lists SET updated_at = ? WHERE id = ?", (now_iso(), list_id))
    audit(conn, "remove_company_from_list", "list", list_id, {"company_id": company_id})
    return {"ok": True}


EXPORT_HEADERS = [
    "cnpj",
    "legal_name",
    "trade_name",
    "status",
    "opening_date",
    "main_cnae_code",
    "main_cnae_description",
    "size",
    "sector",
    "city",
    "state",
    "email",
    "phone",
    "capital_social",
    "opportunity_score",
    "source_name",
    "source_url",
    "collected_at",
    "legal_basis",
]


def export_list(conn, list_id, file_format, purpose):
    purpose = (purpose or "").strip()
    if len(purpose) < 8:
        raise ValueError("Informe uma finalidade de exportacao com pelo menos 8 caracteres")
    rows = conn.execute(
        """
        SELECT %s
        FROM list_companies lc
        JOIN companies c ON c.id = lc.company_id
        WHERE lc.list_id = ?
        ORDER BY c.opportunity_score DESC, c.legal_name ASC
        """
        % ", ".join("c.%s" % header for header in EXPORT_HEADERS),
        (list_id,),
    ).fetchall()
    conn.execute(
        """
        INSERT INTO export_jobs (org_id, user_id, list_id, file_format, declared_purpose, row_count, columns_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ORG_ID, USER_ID, list_id, file_format, purpose, len(rows), json.dumps(EXPORT_HEADERS), now_iso()),
    )
    audit(conn, "export_list", "list", list_id, {"format": file_format, "rows": len(rows), "purpose": purpose})
    if file_format == "xlsx":
        return rows_to_xlsx_bytes(EXPORT_HEADERS, rows, sheet_name="Radar CNPJ"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return rows_to_csv_bytes(EXPORT_HEADERS, rows), "text/csv; charset=utf-8"


def suppression_sets(conn):
    suppressions = {
        normalize_email(row["email"])
        for row in conn.execute("SELECT email FROM suppression_list WHERE org_id = ?", (ORG_ID,)).fetchall()
    }
    opt_outs = {
        normalize_email(row["email"])
        for row in conn.execute("SELECT email FROM opt_outs WHERE org_id = ?", (ORG_ID,)).fetchall()
    }
    return suppressions, opt_outs


def known_shared_domain_set(conn):
    rows = conn.execute("SELECT domain FROM known_shared_domains WHERE org_id = ?", (ORG_ID,)).fetchall()
    return {normalize_domain(row["domain"]) for row in rows}


def normalize_domain(value):
    return str(value or "").strip().lower()


def email_domain(email):
    normalized = normalize_email(email)
    if "@" not in normalized:
        return ""
    return normalized.split("@", 1)[1]


def email_context_counts(conn, email):
    normalized = normalize_email(email)
    domain = email_domain(normalized)
    same_email = conn.execute(
        "SELECT COUNT(DISTINCT cnpj) AS total FROM companies WHERE lower(email) = ?",
        (normalized,),
    ).fetchone()["total"]
    same_domain = 0
    if domain:
        same_domain = conn.execute(
            """
            SELECT COUNT(DISTINCT cnpj) AS total
            FROM companies
            WHERE email IS NOT NULL
              AND email != ''
              AND substr(lower(email), instr(lower(email), '@') + 1) = ?
            """,
            (domain,),
        ).fetchone()["total"]
    return int(same_email or 0), int(same_domain or 0)


def company_partner_names(conn, company_id):
    rows = conn.execute("SELECT name FROM partners WHERE company_id = ?", (company_id,)).fetchall()
    return [row["name"] for row in rows]


def upsert_known_shared_domain(conn, domain, inferred_type, reason):
    domain = normalize_domain(domain)
    if not domain:
        return
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO known_shared_domains (org_id, domain, inferred_type, reason, first_seen_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(domain) DO UPDATE SET
            inferred_type = excluded.inferred_type,
            reason = excluded.reason,
            last_seen_at = excluded.last_seen_at
        """,
        (ORG_ID, domain, inferred_type, reason, timestamp, timestamp),
    )


def persist_email_score(conn, scoring, company_id=None):
    previous = conn.execute(
        """
        SELECT score
        FROM email_classifications
        WHERE email = ? AND (company_id = ? OR (company_id IS NULL AND ? IS NULL))
        ORDER BY id DESC
        LIMIT 1
        """,
        (scoring["email"], company_id, company_id),
    ).fetchone()
    previous_score = previous["score"] if previous else None
    classified_at = now_iso()
    labels_json = json.dumps(scoring["labels"], ensure_ascii=True)
    reasons_json = json.dumps(scoring["reasons"], ensure_ascii=True)
    conn.execute(
        """
        INSERT INTO email_classifications (
            company_id, email, domain, area, classification, score, labels_json,
            reasons_json, is_shared_contact, is_shared_domain,
            shared_company_count, shared_domain_count, algorithm_version, classified_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(company_id, email) DO UPDATE SET
            domain = excluded.domain,
            area = excluded.area,
            classification = excluded.classification,
            score = excluded.score,
            labels_json = excluded.labels_json,
            reasons_json = excluded.reasons_json,
            is_shared_contact = excluded.is_shared_contact,
            is_shared_domain = excluded.is_shared_domain,
            shared_company_count = excluded.shared_company_count,
            shared_domain_count = excluded.shared_domain_count,
            algorithm_version = excluded.algorithm_version,
            classified_at = excluded.classified_at
        """,
        (
            company_id,
            scoring["email"],
            scoring["domain"],
            scoring["area"],
            scoring["classification"],
            scoring["score"],
            labels_json,
            reasons_json,
            1 if "shared_contact" in scoring["labels"] else 0,
            1 if "shared_domain" in scoring["labels"] or "known_shared_domain" in scoring["labels"] else 0,
            scoring["shared_company_count"],
            scoring["shared_domain_count"],
            scoring["algorithm_version"],
            classified_at,
        ),
    )
    conn.execute(
        """
        INSERT INTO email_score_log (company_id, email, previous_score, new_score, reasons_json, algorithm_version, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_id,
            scoring["email"],
            previous_score,
            scoring["score"],
            reasons_json,
            scoring["algorithm_version"],
            classified_at,
        ),
    )


def score_email_record(conn, email, company_id=None):
    email = normalize_email(email)
    if not email and company_id:
        row = conn.execute("SELECT email FROM companies WHERE id = ?", (company_id,)).fetchone()
        email = normalize_email(row["email"] if row else "")
    suppression, opt_out = suppression_sets(conn)
    hygiene = classify_email(email, suppression, opt_out)
    same_email, same_domain = email_context_counts(conn, email)
    partner_names = company_partner_names(conn, company_id) if company_id else []
    known_domains = known_shared_domain_set(conn)
    scoring = score_email(
        email,
        partner_names=partner_names,
        hygiene_result=hygiene,
        same_email_companies=same_email,
        same_domain_companies=same_domain,
        known_shared_domains=known_domains,
        suppression_set=suppression,
        opt_out_set=opt_out,
    )
    if "shared_domain" in scoring["labels"]:
        upsert_known_shared_domain(
            conn,
            scoring["domain"],
            scoring["shared_domain_type"],
            "Dominio aparece em %s CNPJs distintos" % scoring["shared_domain_count"],
        )
    persist_email_score(conn, scoring, company_id=company_id)
    return scoring


def score_emails(conn, emails=None, list_id=None, company_id=None):
    targets = []
    if company_id:
        row = conn.execute("SELECT id, email FROM companies WHERE id = ?", (company_id,)).fetchone()
        if row and row["email"]:
            targets.append((row["id"], row["email"]))
    if list_id:
        rows = conn.execute(
            """
            SELECT c.id, c.email
            FROM list_companies lc
            JOIN companies c ON c.id = lc.company_id
            WHERE lc.list_id = ? AND c.email IS NOT NULL AND c.email != ''
            """,
            (list_id,),
        ).fetchall()
        targets.extend((row["id"], row["email"]) for row in rows)
    for email in emails or []:
        targets.append((None, email))

    results = []
    seen = set()
    for target_company_id, email in targets:
        key = (target_company_id, normalize_email(email))
        if key in seen:
            continue
        seen.add(key)
        results.append(score_email_record(conn, email, company_id=target_company_id))
    audit(conn, "score_emails", "email_classification", list_id or company_id, {"count": len(results)})
    return results


def validate_emails(conn, emails=None, list_id=None):
    emails = emails or []
    company_lookup = {}
    if list_id:
        rows = conn.execute(
            """
            SELECT c.id, c.email
            FROM list_companies lc
            JOIN companies c ON c.id = lc.company_id
            WHERE lc.list_id = ? AND c.email IS NOT NULL AND c.email != ''
            """,
            (list_id,),
        ).fetchall()
        for row in rows:
            company_lookup[normalize_email(row["email"])] = row["id"]
            emails.append(row["email"])

    suppression, opt_out = suppression_sets(conn)
    seen = set()
    results = []
    for email in emails:
        result = classify_email(email, suppression, opt_out, seen)
        company_id = company_lookup.get(result["email"])
        if company_id:
            result["advanced"] = score_email_record(conn, result["email"], company_id=company_id)
        conn.execute(
            """
            INSERT INTO email_validations (email, company_id, list_id, classification, score, reasons, validated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["email"],
                company_id,
                list_id,
                result["classification"],
                result["score"],
                json.dumps(result["reasons"], ensure_ascii=True),
                now_iso(),
            ),
        )
        results.append(result)
    audit(conn, "validate_emails", "email_validation", list_id, {"count": len(results)})
    return results


def add_suppression(conn, email, reason, source="manual"):
    email = normalize_email(email)
    conn.execute(
        """
        INSERT INTO suppression_list (org_id, email, reason, source, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET reason = excluded.reason
        """,
        (ORG_ID, email, reason, source, now_iso()),
    )
    audit(conn, "add_suppression", "suppression", email, {"reason": reason, "source": source})
    return {"email": email, "reason": reason, "source": source}


def assess_lead_eligibility(conn, email, company_id=None):
    email = normalize_email(email)
    if not email:
        return {
            "eligible": False,
            "block_reason": "Lead sem e-mail",
            "hygiene": {"classification": "Invalido", "score": 0, "reasons": ["Lead sem e-mail"]},
            "email_score": {"score": 0, "labels": ["invalid"], "reasons": ["Lead sem e-mail"]},
        }
    suppression, opt_out = suppression_sets(conn)
    hygiene = classify_email(email, suppression, opt_out)
    if hygiene["classification"] in ("Invalido", "Suprimido", "Opt-out"):
        scoring = {
            "email": email,
            "score": 0,
            "labels": ["invalid" if hygiene["classification"] == "Invalido" else "suppressed"],
            "reasons": hygiene.get("reasons") or [],
        }
    else:
        scoring = score_email_record(conn, email, company_id=company_id)
    eligible, block_reason = email_eligibility(email, hygiene, scoring)
    return {
        "eligible": eligible,
        "block_reason": block_reason,
        "hygiene": hygiene,
        "email_score": scoring,
    }


def create_leads_from_list(conn, list_id, source="lista qualificada"):
    base = conn.execute("SELECT id FROM lists WHERE id = ? AND org_id = ?", (list_id, ORG_ID)).fetchone()
    if not base:
        raise ValueError("Lista nao encontrada")
    rows = conn.execute(
        """
        SELECT c.id AS company_id, c.email, c.segment, c.sector, c.main_cnae_code,
               c.opportunity_score
        FROM list_companies lc
        JOIN companies c ON c.id = lc.company_id
        WHERE lc.list_id = ?
        ORDER BY c.opportunity_score DESC, c.legal_name ASC
        """,
        (list_id,),
    ).fetchall()
    created = 0
    updated = 0
    blocked = 0
    eligible_count = 0
    timestamp = now_iso()
    for row in rows:
        email = normalize_email(row["email"])
        existing = conn.execute(
            """
            SELECT id FROM leads
            WHERE org_id = ? AND company_id = ? AND list_id = ? AND email = ?
            """,
            (ORG_ID, row["company_id"], list_id, email),
        ).fetchone()
        eligibility = assess_lead_eligibility(conn, email, row["company_id"])
        email_score = eligibility["email_score"].get("score") or 0
        status = "eligible" if eligibility["eligible"] else "blocked"
        if status == "eligible":
            eligible_count += 1
        else:
            blocked += 1
        score = lead_score(row["opportunity_score"], email_score)
        conn.execute(
            """
            INSERT INTO leads (
                org_id, company_id, list_id, email, segment, source, score,
                status, block_reason, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(org_id, company_id, list_id, email) DO UPDATE SET
                segment = excluded.segment,
                source = excluded.source,
                score = excluded.score,
                status = excluded.status,
                block_reason = excluded.block_reason,
                updated_at = excluded.updated_at
            """,
            (
                ORG_ID,
                row["company_id"],
                list_id,
                email,
                row["segment"] or row["sector"] or row["main_cnae_code"] or "",
                source,
                score,
                status,
                eligibility["block_reason"],
                timestamp,
                timestamp,
            ),
        )
        if existing:
            updated += 1
        else:
            created += 1
    audit(
        conn,
        "create_leads_from_list",
        "list",
        list_id,
        {"created": created, "updated": updated, "eligible": eligible_count, "blocked": blocked},
    )
    return {
        "list_id": list_id,
        "created": created,
        "updated": updated,
        "eligible": eligible_count,
        "blocked": blocked,
        "total": len(rows),
    }


def list_experiment_leads(conn, params=None):
    params = params or {}
    limit = min(int(params.get("limit", 100) or 100), 500)
    where = ["l.org_id = ?"]
    values = [ORG_ID]
    for key, column in [("list_id", "l.list_id"), ("status", "l.status")]:
        value = params.get(key)
        if value:
            where.append("%s = ?" % column)
            values.append(value)
    rows = conn.execute(
        """
        SELECT l.*, c.legal_name, c.trade_name, c.cnpj, c.city, c.state, c.main_cnae_code,
               li.name AS list_name
        FROM leads l
        LEFT JOIN companies c ON c.id = l.company_id
        LEFT JOIN lists li ON li.id = l.list_id
        WHERE %s
        ORDER BY l.score DESC, l.id DESC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [limit],
    ).fetchall()
    return {"items": [dict_row(row) for row in rows]}


def create_campaign(conn, payload):
    name = (payload.get("name") or "").strip()
    subject = (payload.get("subject") or "").strip()
    body = (payload.get("body") or "").strip()
    if not name:
        raise ValueError("Nome da campanha e obrigatorio")
    if not subject:
        raise ValueError("Assunto da campanha e obrigatorio")
    if not body:
        raise ValueError("Corpo da campanha e obrigatorio")
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO campaigns (
            org_id, name, niche, status, subject, body, cta_url,
            daily_limit, interval_seconds, bounce_pause_threshold,
            complaint_pause_threshold, mode, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            name,
            payload.get("niche") or "",
            "draft",
            subject,
            body,
            payload.get("cta_url") or "",
            int(payload.get("daily_limit") or 50),
            int(payload.get("interval_seconds") or 300),
            float(payload.get("bounce_pause_threshold") or 0.02),
            float(payload.get("complaint_pause_threshold") or 0.0005),
            CAMPAIGN_MODE,
            timestamp,
            timestamp,
        ),
    )
    campaign_id = cursor.lastrowid
    conn.execute(
        """
        INSERT INTO campaign_variants (campaign_id, name, subject, body, cta_url, utm_content, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (campaign_id, "A", subject, body, payload.get("cta_url") or "", "variant-a", 1, timestamp),
    )
    audit(conn, "create_campaign", "campaign", campaign_id, {"name": name, "mode": CAMPAIGN_MODE})
    return get_campaign(conn, campaign_id)


def campaign_funnel(conn, campaign_id):
    funnel = empty_funnel()
    planned = conn.execute("SELECT COUNT(*) AS total FROM sends WHERE campaign_id = ?", (campaign_id,)).fetchone()
    funnel["planned"] = int(planned["total"] or 0)
    rows = conn.execute(
        """
        SELECT event_type, COUNT(*) AS total
        FROM events
        WHERE campaign_id = ?
        GROUP BY event_type
        """,
        (campaign_id,),
    ).fetchall()
    for row in rows:
        funnel[row["event_type"]] = int(row["total"] or 0)
    return funnel


def get_campaign(conn, campaign_id):
    campaign = conn.execute("SELECT * FROM campaigns WHERE id = ? AND org_id = ?", (campaign_id, ORG_ID)).fetchone()
    if not campaign:
        return None
    data = dict_row(campaign)
    data["variants"] = [
        dict_row(row)
        for row in conn.execute(
            "SELECT * FROM campaign_variants WHERE campaign_id = ? ORDER BY id",
            (campaign_id,),
        ).fetchall()
    ]
    data["funnel"] = campaign_funnel(conn, campaign_id)
    return data


def list_campaigns(conn):
    rows = conn.execute(
        "SELECT * FROM campaigns WHERE org_id = ? ORDER BY id DESC",
        (ORG_ID,),
    ).fetchall()
    return {"items": [get_campaign(conn, row["id"]) for row in rows]}


def active_campaign_variant(conn, campaign_id):
    variant = conn.execute(
        """
        SELECT *
        FROM campaign_variants
        WHERE campaign_id = ? AND is_active = 1
        ORDER BY id
        LIMIT 1
        """,
        (campaign_id,),
    ).fetchone()
    if not variant:
        raise ValueError("Campanha sem variante ativa")
    return dict_row(variant)


def simulate_campaign(conn, campaign_id, list_id=None, limit=50):
    campaign = conn.execute("SELECT * FROM campaigns WHERE id = ? AND org_id = ?", (campaign_id, ORG_ID)).fetchone()
    if not campaign:
        raise ValueError("Campanha nao encontrada")
    if campaign["mode"] != CAMPAIGN_MODE:
        raise ValueError("O MVP local permite apenas campanhas simuladas")
    if list_id:
        create_leads_from_list(conn, int(list_id), "campanha simulada")
    variant = active_campaign_variant(conn, campaign_id)
    limit = min(int(limit or 50), int(campaign["daily_limit"] or 50), 500)
    where = ["l.org_id = ?"]
    values = [ORG_ID]
    if list_id:
        where.append("l.list_id = ?")
        values.append(int(list_id))
    rows = conn.execute(
        """
        SELECT l.*, c.opportunity_score
        FROM leads l
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE %s
          AND NOT EXISTS (
              SELECT 1 FROM sends s
              WHERE s.lead_id = l.id AND s.campaign_id = ?
          )
        ORDER BY l.score DESC, l.id ASC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [campaign_id, limit],
    ).fetchall()
    timestamp = now_iso()
    sent = 0
    blocked = 0
    for lead in rows:
        eligibility = assess_lead_eligibility(conn, lead["email"], lead["company_id"])
        is_eligible = eligibility["eligible"]
        status = "simulated_sent" if is_eligible else "blocked"
        event_type = "sent" if is_eligible else "blocked"
        block_reason = "" if is_eligible else eligibility["block_reason"]
        if is_eligible:
            sent += 1
        else:
            blocked += 1
        utm_url = append_utm(variant.get("cta_url"), campaign["name"], variant["utm_content"], campaign["niche"])
        cursor = conn.execute(
            """
            INSERT INTO sends (
                lead_id, campaign_id, variant_id, email, status, provider,
                provider_message_id, block_reason, scheduled_at, sent_at, utm_url, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead["id"],
                campaign_id,
                variant["id"],
                lead["email"],
                status,
                PROVIDER,
                "",
                block_reason,
                timestamp,
                timestamp if is_eligible else None,
                utm_url,
                timestamp,
            ),
        )
        send_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO events (send_id, lead_id, campaign_id, event_type, source, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                send_id,
                lead["id"],
                campaign_id,
                event_type,
                "simulated",
                json.dumps({"block_reason": block_reason, "utm_url": utm_url}, ensure_ascii=True),
                timestamp,
            ),
        )
        conn.execute(
            """
            UPDATE leads
            SET status = ?, block_reason = ?, updated_at = ?
            WHERE id = ?
            """,
            ("in_campaign" if is_eligible else "blocked", block_reason, timestamp, lead["id"]),
        )
    if rows:
        conn.execute(
            "UPDATE campaigns SET status = ?, updated_at = ? WHERE id = ?",
            ("running", timestamp, campaign_id),
        )
    audit(
        conn,
        "simulate_campaign",
        "campaign",
        campaign_id,
        {"list_id": list_id, "sent": sent, "blocked": blocked, "attempted": len(rows)},
    )
    result = get_campaign(conn, campaign_id)
    result["simulation"] = {"attempted": len(rows), "sent": sent, "blocked": blocked}
    return result


def utm_from_url(url):
    parsed = urlparse_safe(url)
    return dict(urllib_parse_qsl(parsed.query))


def urlparse_safe(url):
    from urllib.parse import urlparse

    return urlparse(url or "")


def urllib_parse_qsl(query):
    from urllib.parse import parse_qsl

    return parse_qsl(query or "", keep_blank_values=True)


def record_campaign_event(conn, payload):
    send_id = int(payload.get("send_id") or 0)
    event_type = (payload.get("event_type") or "").strip()
    if event_type not in EVENT_STATUS:
        raise ValueError("Tipo de evento invalido")
    row = conn.execute(
        """
        SELECT s.*, l.company_id
        FROM sends s
        JOIN leads l ON l.id = s.lead_id
        WHERE s.id = ?
        """,
        (send_id,),
    ).fetchone()
    if not row:
        raise ValueError("Envio nao encontrado")
    timestamp = now_iso()
    payload_json = json.dumps(payload.get("payload") or {}, ensure_ascii=True)
    conn.execute(
        """
        INSERT INTO events (send_id, lead_id, campaign_id, event_type, source, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (send_id, row["lead_id"], row["campaign_id"], event_type, payload.get("source") or "manual", payload_json, timestamp),
    )
    conn.execute("UPDATE sends SET status = ? WHERE id = ?", (EVENT_STATUS[event_type], send_id))
    if event_type == "replied":
        conn.execute(
            "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
            ("responded", timestamp, row["lead_id"]),
        )
        conn.execute(
            """
            INSERT INTO conversions (lead_id, campaign_id, conversion_type, utm_json, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (row["lead_id"], row["campaign_id"], "reply", json.dumps(utm_from_url(row["utm_url"]), ensure_ascii=True), payload.get("notes") or "", timestamp),
        )
    elif event_type == "converted":
        conn.execute(
            "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
            ("converted", timestamp, row["lead_id"]),
        )
        conn.execute(
            """
            INSERT INTO conversions (lead_id, campaign_id, conversion_type, utm_json, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row["lead_id"],
                row["campaign_id"],
                payload.get("conversion_type") or "signup",
                json.dumps(utm_from_url(row["utm_url"]), ensure_ascii=True),
                payload.get("notes") or "",
                timestamp,
            ),
        )
    elif event_type in ("bounce", "complaint"):
        add_suppression(conn, row["email"], event_type, source="simulated_event")
        conn.execute(
            "UPDATE leads SET status = ?, block_reason = ?, updated_at = ? WHERE id = ?",
            ("blocked", "Evento %s gerou supressao" % event_type, timestamp, row["lead_id"]),
        )
    audit(conn, "record_campaign_event", "send", send_id, {"event_type": event_type})
    return get_campaign(conn, row["campaign_id"])


TEMPLATE_PURPOSES = {"first_contact", "follow_up", "final_follow_up", "reply_to_question", "other"}


def template_version_dict(row):
    data = dict_row(row)
    if not data:
        return None
    data["variables"] = json.loads(data.pop("variables_json") or "[]")
    return data


def get_active_template_version(conn, template_id):
    row = conn.execute(
        """
        SELECT *
        FROM email_template_versions
        WHERE template_id = ? AND is_active = 1
        ORDER BY version_number DESC
        LIMIT 1
        """,
        (template_id,),
    ).fetchone()
    return template_version_dict(row)


def get_email_template(conn, template_id):
    template = conn.execute(
        "SELECT * FROM email_templates WHERE id = ? AND org_id = ?",
        (template_id, ORG_ID),
    ).fetchone()
    if not template:
        return None
    data = dict_row(template)
    versions = [
        template_version_dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM email_template_versions
            WHERE template_id = ?
            ORDER BY version_number DESC
            """,
            (template_id,),
        ).fetchall()
    ]
    data["versions"] = versions
    data["active_version"] = next((version for version in versions if version["is_active"]), versions[0] if versions else None)
    return data


def list_email_templates(conn):
    rows = conn.execute(
        """
        SELECT *
        FROM email_templates
        WHERE org_id = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (ORG_ID,),
    ).fetchall()
    return {"items": [get_email_template(conn, row["id"]) for row in rows]}


def normalize_template_purpose(value):
    purpose = (value or "other").strip()
    return purpose if purpose in TEMPLATE_PURPOSES else "other"


def create_email_template(conn, payload):
    name = (payload.get("name") or "").strip()
    subject = (payload.get("subject") or "").strip()
    body = (payload.get("body") or "").strip()
    if not name:
        raise ValueError("Nome do template e obrigatorio")
    if not subject:
        raise ValueError("Assunto do template e obrigatorio")
    if not body:
        raise ValueError("Corpo do template e obrigatorio")
    validate_editable_template(subject, body)
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO email_templates (org_id, name, purpose, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ORG_ID, name, normalize_template_purpose(payload.get("purpose")), "active", timestamp, timestamp),
    )
    template_id = cursor.lastrowid
    variables = extract_variables(subject, body)
    conn.execute(
        """
        INSERT INTO email_template_versions (
            template_id, version_number, subject, body, variables_json,
            compliance_footer, is_active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            template_id,
            1,
            subject,
            body,
            json.dumps(variables, ensure_ascii=True),
            COMPLIANCE_FOOTER_TEMPLATE,
            1,
            timestamp,
        ),
    )
    audit(conn, "create_email_template", "email_template", template_id, {"name": name, "variables": variables})
    return get_email_template(conn, template_id)


def create_email_template_version(conn, template_id, payload):
    template = get_email_template(conn, template_id)
    if not template:
        raise ValueError("Template nao encontrado")
    active = template.get("active_version") or {}
    subject = (payload.get("subject") if payload.get("subject") is not None else active.get("subject") or "").strip()
    body = (payload.get("body") if payload.get("body") is not None else active.get("body") or "").strip()
    if not subject:
        raise ValueError("Assunto do template e obrigatorio")
    if not body:
        raise ValueError("Corpo do template e obrigatorio")
    validate_editable_template(subject, body)
    version_number = int(active.get("version_number") or 0) + 1
    variables = extract_variables(subject, body)
    timestamp = now_iso()
    conn.execute("UPDATE email_template_versions SET is_active = 0 WHERE template_id = ?", (template_id,))
    conn.execute(
        """
        INSERT INTO email_template_versions (
            template_id, version_number, subject, body, variables_json,
            compliance_footer, is_active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            template_id,
            version_number,
            subject,
            body,
            json.dumps(variables, ensure_ascii=True),
            COMPLIANCE_FOOTER_TEMPLATE,
            1,
            timestamp,
        ),
    )
    conn.execute("UPDATE email_templates SET updated_at = ? WHERE id = ?", (timestamp, template_id))
    audit(
        conn,
        "create_email_template_version",
        "email_template",
        template_id,
        {"version_number": version_number, "variables": variables},
    )
    return get_email_template(conn, template_id)


def template_version_for_render(conn, template_id=None, template_version_id=None):
    if template_version_id:
        row = conn.execute(
            """
            SELECT v.*, t.name, t.purpose, t.org_id
            FROM email_template_versions v
            JOIN email_templates t ON t.id = v.template_id
            WHERE v.id = ? AND t.org_id = ?
            """,
            (int(template_version_id), ORG_ID),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT v.*, t.name, t.purpose, t.org_id
            FROM email_template_versions v
            JOIN email_templates t ON t.id = v.template_id
            WHERE v.template_id = ? AND t.org_id = ? AND v.is_active = 1
            ORDER BY v.version_number DESC
            LIMIT 1
            """,
            (int(template_id or 0), ORG_ID),
        ).fetchone()
    return row


def render_email_template(conn, payload):
    version = template_version_for_render(
        conn,
        template_id=payload.get("template_id"),
        template_version_id=payload.get("template_version_id"),
    )
    if not version:
        raise ValueError("Versao de template nao encontrada")
    company_id = payload.get("company_id")
    context = {}
    context_source = "manual"
    if company_id:
        company = get_company(conn, int(company_id))
        if not company:
            raise ValueError("Empresa nao encontrada")
        context = build_company_template_context(company, company.get("partners") or [], payload.get("cta_url") or "")
        context_source = "company"
    context.update(payload.get("context") or {})
    if payload.get("cta_url"):
        context["cta_url"] = payload.get("cta_url")
    rendered = render_template(
        version["subject"],
        version["body"],
        company_context=context,
        unsubscribe_url=payload.get("unsubscribe_url"),
        privacy_url=payload.get("privacy_url"),
    )
    variables = json.loads(version["variables_json"] or "[]")
    unsupported = [variable for variable in variables if variable not in SUPPORTED_VARIABLES]
    result = {
        "template_id": version["template_id"],
        "template_version_id": version["id"],
        "version_number": version["version_number"],
        "name": version["name"],
        "purpose": version["purpose"],
        "context_source": context_source,
        "supported_variables": sorted(SUPPORTED_VARIABLES),
        "unsupported_variables": unsupported,
    }
    result.update(rendered)
    audit(
        conn,
        "render_email_template",
        "email_template",
        version["template_id"],
        {"version_id": version["id"], "company_id": company_id, "missing": rendered["missing_variables"]},
    )
    return result


def sequence_step_dict(row):
    return dict_row(row)


def get_sequence(conn, sequence_id):
    sequence = conn.execute(
        "SELECT * FROM sequences WHERE id = ? AND org_id = ?",
        (sequence_id, ORG_ID),
    ).fetchone()
    if not sequence:
        return None
    data = dict_row(sequence)
    data["steps"] = [
        sequence_step_dict(row)
        for row in conn.execute(
            """
            SELECT ss.*, t.name AS template_name, v.version_number AS template_version_number
            FROM sequence_steps ss
            JOIN email_templates t ON t.id = ss.template_id
            JOIN email_template_versions v ON v.id = ss.template_version_id
            WHERE ss.sequence_id = ?
            ORDER BY ss.step_number
            """,
            (sequence_id,),
        ).fetchall()
    ]
    counts = conn.execute(
        """
        SELECT status, COUNT(*) AS total
        FROM lead_journey
        WHERE sequence_id = ?
        GROUP BY status
        """,
        (sequence_id,),
    ).fetchall()
    data["journey_counts"] = dict((row["status"], row["total"]) for row in counts)
    return data


def list_sequences(conn):
    rows = conn.execute(
        "SELECT id FROM sequences WHERE org_id = ? ORDER BY updated_at DESC, id DESC",
        (ORG_ID,),
    ).fetchall()
    return {"items": [get_sequence(conn, row["id"]) for row in rows]}


def resolve_template_version(conn, template_id=None, template_version_id=None):
    version = template_version_for_render(
        conn,
        template_id=template_id,
        template_version_id=template_version_id,
    )
    if not version:
        raise ValueError("Template versionado nao encontrado")
    return dict_row(version)


def create_sequence(conn, payload):
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Nome da sequencia e obrigatorio")
    steps = payload.get("steps") or []
    if not steps:
        raise ValueError("Informe ao menos um passo")
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO sequences (org_id, name, description, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ORG_ID, name, payload.get("description") or "", "active", timestamp, timestamp),
    )
    sequence_id = cursor.lastrowid
    for index, step in enumerate(steps, start=1):
        version = resolve_template_version(
            conn,
            template_id=step.get("template_id"),
            template_version_id=step.get("template_version_id"),
        )
        conn.execute(
            """
            INSERT INTO sequence_steps (
                sequence_id, step_number, name, step_type, wait_days,
                template_id, template_version_id, require_approval, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sequence_id,
                int(step.get("step_number") or index),
                step.get("name") or "Passo %s" % index,
                "email",
                max(int(step.get("wait_days") or 0), 0),
                version["template_id"],
                version["id"],
                1 if step.get("require_approval", True) is not False else 0,
                timestamp,
            ),
        )
    audit(conn, "create_sequence", "sequence", sequence_id, {"name": name, "steps": len(steps)})
    return get_sequence(conn, sequence_id)


def first_sequence_step(conn, sequence_id):
    return conn.execute(
        "SELECT * FROM sequence_steps WHERE sequence_id = ? ORDER BY step_number LIMIT 1",
        (sequence_id,),
    ).fetchone()


def next_sequence_step(conn, sequence_id, current_step_number):
    return conn.execute(
        """
        SELECT *
        FROM sequence_steps
        WHERE sequence_id = ? AND step_number > ?
        ORDER BY step_number
        LIMIT 1
        """,
        (sequence_id, int(current_step_number or 0)),
    ).fetchone()


def log_agent_action(conn, lead_id, sequence_id, action_type, source, reason, payload=None):
    conn.execute(
        """
        INSERT INTO agent_actions (org_id, lead_id, sequence_id, action_type, source, reason, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            lead_id,
            sequence_id,
            action_type,
            source,
            reason,
            json.dumps(payload or {}, ensure_ascii=True),
            now_iso(),
        ),
    )


def journey_context(conn, journey_id):
    row = conn.execute(
        """
        SELECT lj.*, l.email, l.company_id, l.score AS lead_score, c.legal_name, c.trade_name,
               c.cnpj, c.city, c.state, s.name AS sequence_name, ss.name AS step_name,
               ss.template_id, ss.template_version_id, ss.wait_days
        FROM lead_journey lj
        JOIN leads l ON l.id = lj.lead_id
        LEFT JOIN companies c ON c.id = l.company_id
        JOIN sequences s ON s.id = lj.sequence_id
        JOIN sequence_steps ss ON ss.id = lj.current_step_id
        WHERE lj.id = ? AND lj.org_id = ?
        """,
        (journey_id, ORG_ID),
    ).fetchone()
    return dict_row(row)


def create_step_approval(conn, journey_id):
    context = journey_context(conn, journey_id)
    if not context:
        raise ValueError("Jornada nao encontrada")
    existing = conn.execute(
        """
        SELECT id
        FROM approval_queue
        WHERE item_type = 'sequence_step'
          AND item_id = ?
          AND status = 'pending'
        ORDER BY id DESC
        LIMIT 1
        """,
        (journey_id,),
    ).fetchone()
    if existing:
        return existing["id"]
    rendered = render_email_template(
        conn,
        {
            "template_version_id": context["template_version_id"],
            "company_id": context["company_id"],
            "cta_url": "",
        },
    )
    title = "Aprovar %s para %s" % (
        context["step_name"],
        context.get("trade_name") or context.get("legal_name") or context["email"],
    )
    payload = {
        "journey_id": journey_id,
        "lead_id": context["lead_id"],
        "sequence_id": context["sequence_id"],
        "sequence_name": context["sequence_name"],
        "step_id": context["current_step_id"],
        "step_number": context["current_step_number"],
        "step_name": context["step_name"],
        "email": context["email"],
        "company_id": context["company_id"],
        "company_name": context.get("trade_name") or context.get("legal_name") or "",
        "subject": rendered["subject"],
        "body": rendered["body"],
        "missing_variables": rendered["missing_variables"],
        "template_version_id": context["template_version_id"],
    }
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO approval_queue (org_id, item_type, item_id, status, title, context_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (ORG_ID, "sequence_step", journey_id, "pending", title, json.dumps(payload, ensure_ascii=True), timestamp),
    )
    log_agent_action(
        conn,
        context["lead_id"],
        context["sequence_id"],
        "approval_requested",
        "system",
        "Passo renderizado e enviado para aprovacao humana",
        payload,
    )
    return cursor.lastrowid


def enroll_sequence_from_list(conn, sequence_id, list_id):
    sequence = get_sequence(conn, sequence_id)
    if not sequence:
        raise ValueError("Sequencia nao encontrada")
    first_step = first_sequence_step(conn, sequence_id)
    if not first_step:
        raise ValueError("Sequencia sem passos")
    create_leads_from_list(conn, int(list_id), "sequencia semi-supervisionada")
    leads = conn.execute(
        """
        SELECT *
        FROM leads
        WHERE org_id = ? AND list_id = ? AND status = 'eligible'
        ORDER BY score DESC, id ASC
        """,
        (ORG_ID, int(list_id)),
    ).fetchall()
    timestamp = now_iso()
    enrolled = 0
    existing = 0
    approvals = 0
    for lead in leads:
        before = conn.execute(
            "SELECT id FROM lead_journey WHERE org_id = ? AND lead_id = ? AND sequence_id = ?",
            (ORG_ID, lead["id"], sequence_id),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO lead_journey (
                org_id, lead_id, sequence_id, current_step_id, current_step_number,
                status, next_action_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(org_id, lead_id, sequence_id) DO NOTHING
            """,
            (
                ORG_ID,
                lead["id"],
                sequence_id,
                first_step["id"],
                first_step["step_number"],
                "pending_approval",
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        journey = conn.execute(
            "SELECT id FROM lead_journey WHERE org_id = ? AND lead_id = ? AND sequence_id = ?",
            (ORG_ID, lead["id"], sequence_id),
        ).fetchone()
        if before:
            existing += 1
        else:
            enrolled += 1
            approvals += 1 if create_step_approval(conn, journey["id"]) else 0
    audit(
        conn,
        "enroll_sequence_from_list",
        "sequence",
        sequence_id,
        {"list_id": list_id, "enrolled": enrolled, "existing": existing, "approvals": approvals},
    )
    return {"sequence_id": sequence_id, "list_id": list_id, "enrolled": enrolled, "existing": existing, "approvals": approvals}


def list_journeys(conn, params=None):
    params = params or {}
    where = ["lj.org_id = ?"]
    values = [ORG_ID]
    if params.get("sequence_id"):
        where.append("lj.sequence_id = ?")
        values.append(int(params.get("sequence_id")))
    if params.get("status"):
        where.append("lj.status = ?")
        values.append(params.get("status"))
    rows = conn.execute(
        """
        SELECT lj.*, l.email, l.score AS lead_score, c.legal_name, c.trade_name,
               s.name AS sequence_name, ss.name AS step_name
        FROM lead_journey lj
        JOIN leads l ON l.id = lj.lead_id
        LEFT JOIN companies c ON c.id = l.company_id
        JOIN sequences s ON s.id = lj.sequence_id
        LEFT JOIN sequence_steps ss ON ss.id = lj.current_step_id
        WHERE %s
        ORDER BY lj.updated_at DESC, lj.id DESC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [min(int(params.get("limit", 200) or 200), 500)],
    ).fetchall()
    return {"items": [dict_row(row) for row in rows]}


def parse_approval_row(row):
    data = dict_row(row)
    if not data:
        return None
    data["context"] = json.loads(data.pop("context_json") or "{}")
    return data


def list_approvals(conn, params=None):
    params = params or {}
    status = params.get("status") or "pending"
    rows = conn.execute(
        """
        SELECT *
        FROM approval_queue
        WHERE org_id = ? AND status = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (ORG_ID, status, min(int(params.get("limit", 100) or 100), 500)),
    ).fetchall()
    return {"items": [parse_approval_row(row) for row in rows]}


def ensure_sequence_campaign(conn, sequence_id):
    sequence = conn.execute("SELECT * FROM sequences WHERE id = ? AND org_id = ?", (sequence_id, ORG_ID)).fetchone()
    if not sequence:
        raise ValueError("Sequencia nao encontrada")
    if sequence["campaign_id"]:
        existing = conn.execute("SELECT id FROM campaigns WHERE id = ?", (sequence["campaign_id"],)).fetchone()
        if existing:
            return sequence["campaign_id"]
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO campaigns (
            org_id, name, niche, status, subject, body, cta_url,
            daily_limit, interval_seconds, bounce_pause_threshold,
            complaint_pause_threshold, mode, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            "Sequencia: %s" % sequence["name"],
            "sequence",
            "running",
            "Sequencia semi-supervisionada",
            "Conteudo renderizado por passo.",
            "",
            50,
            300,
            0.02,
            0.0005,
            CAMPAIGN_MODE,
            timestamp,
            timestamp,
        ),
    )
    campaign_id = cursor.lastrowid
    conn.execute("UPDATE sequences SET campaign_id = ?, updated_at = ? WHERE id = ?", (campaign_id, timestamp, sequence_id))
    return campaign_id


def ensure_sequence_variant(conn, campaign_id, step, rendered):
    utm_content = "sequence-step-%s" % step["step_number"]
    existing = conn.execute(
        "SELECT id FROM campaign_variants WHERE campaign_id = ? AND utm_content = ?",
        (campaign_id, utm_content),
    ).fetchone()
    if existing:
        return existing["id"]
    cursor = conn.execute(
        """
        INSERT INTO campaign_variants (campaign_id, name, subject, body, cta_url, utm_content, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            campaign_id,
            step["name"],
            rendered.get("subject") or "",
            rendered.get("body") or "",
            "",
            utm_content,
            1,
            now_iso(),
        ),
    )
    return cursor.lastrowid


def approve_sequence_step(conn, approval_id, note=""):
    approval = conn.execute(
        "SELECT * FROM approval_queue WHERE id = ? AND org_id = ?",
        (approval_id, ORG_ID),
    ).fetchone()
    if not approval:
        raise ValueError("Aprovacao nao encontrada")
    if approval["status"] != "pending":
        raise ValueError("Aprovacao ja decidida")
    context = json.loads(approval["context_json"] or "{}")
    journey = journey_context(conn, int(context["journey_id"]))
    if not journey:
        raise ValueError("Jornada nao encontrada")
    if journey["status"] != "pending_approval":
        raise ValueError("Jornada nao esta pendente de aprovacao")
    step = conn.execute("SELECT * FROM sequence_steps WHERE id = ?", (journey["current_step_id"],)).fetchone()
    campaign_id = ensure_sequence_campaign(conn, journey["sequence_id"])
    rendered = {"subject": context.get("subject") or "", "body": context.get("body") or ""}
    variant_id = ensure_sequence_variant(conn, campaign_id, step, rendered)
    timestamp = now_iso()
    utm_url = append_utm("", "Sequencia %s" % journey["sequence_id"], "sequence-step-%s" % step["step_number"], "sequence")
    conn.execute(
        """
        INSERT OR IGNORE INTO sends (
            lead_id, campaign_id, variant_id, email, status, provider,
            provider_message_id, block_reason, scheduled_at, sent_at, utm_url, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            journey["lead_id"],
            campaign_id,
            variant_id,
            journey["email"],
            "simulated_sent",
            PROVIDER,
            "",
            "",
            timestamp,
            timestamp,
            utm_url,
            timestamp,
        ),
    )
    send = conn.execute(
        "SELECT id FROM sends WHERE lead_id = ? AND campaign_id = ? AND variant_id = ?",
        (journey["lead_id"], campaign_id, variant_id),
    ).fetchone()
    conn.execute(
        """
        INSERT INTO events (send_id, lead_id, campaign_id, event_type, source, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            send["id"],
            journey["lead_id"],
            campaign_id,
            "sent",
            "simulated",
            json.dumps({"approval_id": approval_id, "sequence_id": journey["sequence_id"], "step_id": step["id"]}, ensure_ascii=True),
            timestamp,
        ),
    )
    next_step = next_sequence_step(conn, journey["sequence_id"], step["step_number"])
    if next_step:
        next_action_at = (datetime.utcnow() + timedelta(days=int(next_step["wait_days"] or 0))).replace(microsecond=0).isoformat() + "Z"
        status = "waiting"
        current_step_id = next_step["id"]
        current_step_number = next_step["step_number"]
    else:
        next_action_at = None
        status = "completed"
        current_step_id = step["id"]
        current_step_number = step["step_number"]
    conn.execute(
        """
        UPDATE lead_journey
        SET status = ?, current_step_id = ?, current_step_number = ?,
            next_action_at = ?, last_action_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, current_step_id, current_step_number, next_action_at, timestamp, timestamp, journey["id"]),
    )
    conn.execute(
        "UPDATE approval_queue SET status = ?, decided_at = ?, decision_note = ? WHERE id = ?",
        ("approved", timestamp, note or "", approval_id),
    )
    log_agent_action(
        conn,
        journey["lead_id"],
        journey["sequence_id"],
        "step_approved_and_simulated",
        "human",
        note or "Aprovacao humana executou passo simulado",
        {"approval_id": approval_id, "send_id": send["id"], "step_id": step["id"], "next_status": status},
    )
    audit(conn, "approve_sequence_step", "approval", approval_id, {"send_id": send["id"], "journey_status": status})
    return {"approval": parse_approval_row(conn.execute("SELECT * FROM approval_queue WHERE id = ?", (approval_id,)).fetchone()), "journey": journey_context(conn, journey["id"]), "send_id": send["id"]}


def reject_sequence_step(conn, approval_id, note=""):
    approval = conn.execute(
        "SELECT * FROM approval_queue WHERE id = ? AND org_id = ?",
        (approval_id, ORG_ID),
    ).fetchone()
    if not approval:
        raise ValueError("Aprovacao nao encontrada")
    if approval["status"] != "pending":
        raise ValueError("Aprovacao ja decidida")
    context = json.loads(approval["context_json"] or "{}")
    journey = journey_context(conn, int(context["journey_id"]))
    timestamp = now_iso()
    conn.execute(
        "UPDATE approval_queue SET status = ?, decided_at = ?, decision_note = ? WHERE id = ?",
        ("rejected", timestamp, note or "", approval_id),
    )
    if journey:
        conn.execute(
            "UPDATE lead_journey SET status = ?, block_reason = ?, updated_at = ? WHERE id = ?",
            ("rejected", note or "Rejeitado por humano", timestamp, journey["id"]),
        )
        log_agent_action(
            conn,
            journey["lead_id"],
            journey["sequence_id"],
            "step_rejected",
            "human",
            note or "Passo rejeitado por humano",
            {"approval_id": approval_id, "step_id": context.get("step_id")},
        )
    audit(conn, "reject_sequence_step", "approval", approval_id, {"note": note})
    return {"approval": parse_approval_row(conn.execute("SELECT * FROM approval_queue WHERE id = ?", (approval_id,)).fetchone())}


def prepare_next_journey_step(conn, journey_id):
    journey = conn.execute("SELECT * FROM lead_journey WHERE id = ? AND org_id = ?", (journey_id, ORG_ID)).fetchone()
    if not journey:
        raise ValueError("Jornada nao encontrada")
    if journey["status"] != "waiting":
        raise ValueError("Jornada nao esta aguardando proximo passo")
    timestamp = now_iso()
    conn.execute(
        "UPDATE lead_journey SET status = ?, updated_at = ? WHERE id = ?",
        ("pending_approval", timestamp, journey_id),
    )
    approval_id = create_step_approval(conn, journey_id)
    audit(conn, "prepare_next_journey_step", "lead_journey", journey_id, {"approval_id": approval_id})
    return {"journey": journey_context(conn, journey_id), "approval_id": approval_id}


def list_agent_actions(conn, params=None):
    params = params or {}
    rows = conn.execute(
        """
        SELECT aa.*, l.email, s.name AS sequence_name
        FROM agent_actions aa
        LEFT JOIN leads l ON l.id = aa.lead_id
        LEFT JOIN sequences s ON s.id = aa.sequence_id
        WHERE aa.org_id = ?
        ORDER BY aa.id DESC
        LIMIT ?
        """,
        (ORG_ID, min(int(params.get("limit", 100) or 100), 500)),
    ).fetchall()
    items = []
    for row in rows:
        data = dict_row(row)
        data["payload"] = json.loads(data.pop("payload_json") or "{}")
        items.append(data)
    return {"items": items}


ICP_CRITERIA_KEYS = {
    "states",
    "cities",
    "cnaes",
    "sectors",
    "sizes",
    "min_opportunity_score",
    "min_email_score",
    "require_email",
    "require_corporate_email",
    "exclude_shared_email",
    "exclude_suppressed",
    "max_leads",
}


def split_criteria_values(value, digits=False):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = re.split(r"[,;\n]+", str(value))
    cleaned = []
    for item in items:
        text = str(item or "").strip()
        if digits:
            text = only_digits(text)
        if text:
            cleaned.append(text)
    return cleaned


def bool_criteria(value, default=False):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "sim", "on")


def int_criteria(value, default=0, minimum=0, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def normalize_icp_criteria(payload):
    criteria = dict(payload or {})
    normalized = {
        "states": [item.upper() for item in split_criteria_values(criteria.get("states"))],
        "cities": [item.lower() for item in split_criteria_values(criteria.get("cities"))],
        "cnaes": split_criteria_values(criteria.get("cnaes"), digits=True),
        "sectors": [item.lower() for item in split_criteria_values(criteria.get("sectors"))],
        "sizes": [item.lower() for item in split_criteria_values(criteria.get("sizes"))],
        "min_opportunity_score": int_criteria(criteria.get("min_opportunity_score"), 0, 0, 100),
        "min_email_score": int_criteria(criteria.get("min_email_score"), 30, 0, 100),
        "require_email": bool_criteria(criteria.get("require_email"), True),
        "require_corporate_email": bool_criteria(criteria.get("require_corporate_email"), True),
        "exclude_shared_email": bool_criteria(criteria.get("exclude_shared_email"), True),
        "exclude_suppressed": bool_criteria(criteria.get("exclude_suppressed"), True),
        "max_leads": int_criteria(criteria.get("max_leads"), 50, 1, 500),
    }
    return normalized


def criteria_payload_from_request(payload):
    if payload.get("criteria") and isinstance(payload.get("criteria"), dict):
        return payload["criteria"]
    return {key: payload.get(key) for key in ICP_CRITERIA_KEYS if key in payload}


def parse_icp_rule_row(row):
    data = dict_row(row)
    if not data:
        return None
    data["criteria"] = json.loads(data.pop("criteria_json") or "{}")
    return data


def create_icp_rule(conn, payload):
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Nome do ICP e obrigatorio")
    status = (payload.get("status") or "active").strip()
    if status not in ("draft", "active", "archived"):
        raise ValueError("Status de ICP invalido")
    criteria = normalize_icp_criteria(criteria_payload_from_request(payload))
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO icp_rules (org_id, name, description, status, criteria_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            name,
            payload.get("description") or "",
            status,
            json.dumps(criteria, ensure_ascii=True),
            timestamp,
            timestamp,
        ),
    )
    audit(conn, "create_icp_rule", "icp_rule", cursor.lastrowid, {"name": name, "criteria": criteria})
    return get_icp_rule(conn, cursor.lastrowid)


def get_icp_rule(conn, rule_id):
    row = conn.execute(
        "SELECT * FROM icp_rules WHERE id = ? AND org_id = ?",
        (rule_id, ORG_ID),
    ).fetchone()
    return parse_icp_rule_row(row)


def list_icp_rules(conn, params=None):
    params = params or {}
    where = ["org_id = ?"]
    values = [ORG_ID]
    if params.get("status"):
        where.append("status = ?")
        values.append(params.get("status"))
    rows = conn.execute(
        """
        SELECT *
        FROM icp_rules
        WHERE %s
        ORDER BY id DESC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [min(int(params.get("limit", 100) or 100), 500)],
    ).fetchall()
    return {"items": [parse_icp_rule_row(row) for row in rows]}


def cnae_matches(value, expected):
    digits = only_digits(value)
    if not expected:
        return True
    return any(digits.startswith(item) for item in expected if item)


def row_text(row, key):
    return str(row[key] or "").strip()


def lower_row_text(row, key):
    return row_text(row, key).lower()


def add_match(reasons, label, value):
    if value:
        reasons.append("%s: %s" % (label, value))
    else:
        reasons.append(label)


def evaluate_icp_candidate(conn, row, rule):
    criteria = rule["criteria"]
    matched = []
    blocked = []
    company_score = int(row["opportunity_score"] or 0)
    email = normalize_email(row["email"])
    digital_score = int(row["digital_maturity_score"] or 0)
    email_score = 0
    email_labels = []
    hygiene = {}

    status = lower_row_text(row, "status")
    if status and "ativa" not in status:
        blocked.append("Situacao cadastral nao ativa: %s" % row_text(row, "status"))

    if criteria["states"]:
        if row_text(row, "state").upper() not in criteria["states"]:
            blocked.append("UF fora do ICP: %s" % row_text(row, "state"))
        else:
            add_match(matched, "UF dentro do ICP", row_text(row, "state"))

    if criteria["cities"]:
        if lower_row_text(row, "city") not in criteria["cities"]:
            blocked.append("Cidade fora do ICP: %s" % row_text(row, "city"))
        else:
            add_match(matched, "Cidade dentro do ICP", row_text(row, "city"))

    if criteria["cnaes"]:
        if not cnae_matches(row_text(row, "main_cnae_code"), criteria["cnaes"]):
            blocked.append("CNAE fora do ICP: %s" % row_text(row, "main_cnae_code"))
        else:
            add_match(matched, "CNAE dentro do ICP", row_text(row, "main_cnae_code"))

    if criteria["sectors"]:
        if lower_row_text(row, "sector") not in criteria["sectors"]:
            blocked.append("Setor fora do ICP: %s" % row_text(row, "sector"))
        else:
            add_match(matched, "Setor dentro do ICP", row_text(row, "sector"))

    if criteria["sizes"]:
        if lower_row_text(row, "size") not in criteria["sizes"]:
            blocked.append("Porte fora do ICP: %s" % row_text(row, "size"))
        else:
            add_match(matched, "Porte dentro do ICP", row_text(row, "size"))

    if company_score < criteria["min_opportunity_score"]:
        blocked.append("Score da empresa abaixo do ICP: %s" % company_score)
    elif criteria["min_opportunity_score"]:
        add_match(matched, "Score da empresa atingiu minimo", company_score)

    if criteria["require_email"] and not email:
        blocked.append("ICP exige e-mail")

    if email:
        eligibility = assess_lead_eligibility(conn, email, row["company_id"])
        hygiene = eligibility["hygiene"]
        scoring = eligibility["email_score"]
        email_score = int(scoring.get("score") or 0)
        email_labels = scoring.get("labels") or []
        if criteria["exclude_suppressed"] and hygiene.get("classification") in ("Suprimido", "Opt-out"):
            blocked.append("E-mail em supressao/opt-out")
        if not eligibility["eligible"]:
            blocked.append(eligibility["block_reason"])
        if email_score < criteria["min_email_score"]:
            blocked.append("Score de e-mail abaixo do ICP: %s" % email_score)
        else:
            add_match(matched, "Score de e-mail atingiu minimo", email_score)
        if criteria["require_corporate_email"] and "personal_domain" in email_labels:
            blocked.append("ICP exige e-mail corporativo")
        if criteria["exclude_shared_email"] and set(email_labels) & {"shared_contact", "shared_domain", "known_shared_domain"}:
            blocked.append("ICP bloqueia contato compartilhado/terceirizado")

    if digital_score:
        add_match(matched, "Maturidade digital disponivel", digital_score)

    fit_score = min(100, 35 + (len(matched) * 10))
    priority_score = int(round((company_score * 0.40) + (email_score * 0.35) + (fit_score * 0.20) + (digital_score * 0.05)))
    reason = {
        "matched": matched,
        "blocked": blocked,
        "company_score": company_score,
        "email_score": email_score,
        "email_labels": email_labels,
        "hygiene_classification": hygiene.get("classification", ""),
        "digital_maturity_score": digital_score,
        "fit_score": fit_score,
        "priority_score": priority_score,
        "criteria": criteria,
    }
    return {
        "matched": not blocked,
        "blocked": blocked,
        "reason": reason,
        "fit_score": fit_score,
        "priority_score": priority_score,
    }


def icp_candidate_rows(conn, criteria, list_id=None):
    limit = min(max(criteria["max_leads"] * 10, criteria["max_leads"]), 1000)
    if list_id:
        base = conn.execute("SELECT id FROM lists WHERE id = ? AND org_id = ?", (list_id, ORG_ID)).fetchone()
        if not base:
            raise ValueError("Lista nao encontrada")
        return conn.execute(
            """
            SELECT c.id AS company_id, c.cnpj, c.legal_name, c.trade_name, c.status,
                   c.city, c.state, c.main_cnae_code, c.main_cnae_description,
                   c.size, c.email, c.sector, c.opportunity_score,
                   l.id AS lead_id, l.status AS lead_status, l.block_reason AS lead_block_reason,
                   ce.digital_maturity_score
            FROM list_companies lc
            JOIN companies c ON c.id = lc.company_id
            LEFT JOIN leads l ON l.company_id = c.id AND l.list_id = lc.list_id AND l.org_id = ?
            LEFT JOIN company_enrichment ce ON ce.company_id = c.id
            WHERE lc.list_id = ?
            ORDER BY c.opportunity_score DESC, c.legal_name ASC
            LIMIT ?
            """,
            (ORG_ID, int(list_id), limit),
        ).fetchall()
    return conn.execute(
        """
        SELECT c.id AS company_id, c.cnpj, c.legal_name, c.trade_name, c.status,
               c.city, c.state, c.main_cnae_code, c.main_cnae_description,
               c.size, c.email, c.sector, c.opportunity_score,
               NULL AS lead_id, NULL AS lead_status, NULL AS lead_block_reason,
               ce.digital_maturity_score
        FROM companies c
        LEFT JOIN company_enrichment ce ON ce.company_id = c.id
        ORDER BY c.opportunity_score DESC, c.legal_name ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def existing_priority_item(conn, rule_id, company_id, list_id=None):
    if list_id is None:
        return conn.execute(
            """
            SELECT *
            FROM lead_priority_queue
            WHERE org_id = ? AND icp_rule_id = ? AND company_id = ? AND list_id IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (ORG_ID, rule_id, company_id),
        ).fetchone()
    return conn.execute(
        """
        SELECT *
        FROM lead_priority_queue
        WHERE org_id = ? AND icp_rule_id = ? AND company_id = ? AND list_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (ORG_ID, rule_id, company_id, int(list_id)),
    ).fetchone()


def upsert_priority_item(conn, rule, row, evaluation, list_id=None):
    existing = existing_priority_item(conn, rule["id"], row["company_id"], list_id)
    timestamp = now_iso()
    reason_json = json.dumps(evaluation["reason"], ensure_ascii=True)
    if existing:
        if existing["status"] in ("accepted", "rejected", "enrolled"):
            return None, "existing_decided"
        conn.execute(
            """
            UPDATE lead_priority_queue
            SET lead_id = ?, status = ?, priority_score = ?, fit_score = ?,
                reason_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                row["lead_id"],
                "suggested",
                evaluation["priority_score"],
                evaluation["fit_score"],
                reason_json,
                timestamp,
                existing["id"],
            ),
        )
        return existing["id"], "updated"
    cursor = conn.execute(
        """
        INSERT INTO lead_priority_queue (
            org_id, icp_rule_id, lead_id, company_id, list_id, status,
            priority_score, fit_score, reason_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            rule["id"],
            row["lead_id"],
            row["company_id"],
            int(list_id) if list_id else None,
            "suggested",
            evaluation["priority_score"],
            evaluation["fit_score"],
            reason_json,
            timestamp,
            timestamp,
        ),
    )
    return cursor.lastrowid, "created"


def prioritize_icp_rule(conn, rule_id, list_id=None, limit=None):
    rule = get_icp_rule(conn, rule_id)
    if not rule:
        raise ValueError("ICP nao encontrado")
    if rule["status"] == "archived":
        raise ValueError("ICP arquivado nao pode priorizar")
    criteria = dict(rule["criteria"])
    if limit:
        criteria["max_leads"] = int_criteria(limit, criteria["max_leads"], 1, 500)
        rule["criteria"] = criteria
    if list_id:
        create_leads_from_list(conn, int(list_id), "priorizacao ICP")
    rows = icp_candidate_rows(conn, criteria, list_id=list_id)
    suggested = 0
    updated = 0
    skipped_existing = 0
    blocked = 0
    blocked_reasons = {}
    for row in rows:
        if suggested >= criteria["max_leads"]:
            break
        evaluation = evaluate_icp_candidate(conn, row, rule)
        if not evaluation["matched"]:
            blocked += 1
            for reason in evaluation["blocked"]:
                blocked_reasons[reason] = blocked_reasons.get(reason, 0) + 1
            continue
        item_id, state = upsert_priority_item(conn, rule, row, evaluation, list_id=list_id)
        if not item_id:
            skipped_existing += 1
            continue
        if state == "created":
            suggested += 1
        else:
            updated += 1
    summary = {
        "evaluated": len(rows),
        "suggested": suggested,
        "updated": updated,
        "blocked": blocked,
        "skipped_existing": skipped_existing,
        "blocked_reasons": blocked_reasons,
        "list_id": int(list_id) if list_id else None,
        "max_leads": criteria["max_leads"],
    }
    log_agent_action(
        conn,
        None,
        None,
        "icp_prioritized",
        "system",
        "ICP %s priorizou %s leads elegiveis" % (rule["name"], suggested + updated),
        {"icp_rule_id": rule["id"], "summary": summary},
    )
    audit(conn, "prioritize_icp_rule", "icp_rule", rule["id"], summary)
    return {"icp_rule": get_icp_rule(conn, rule["id"]), "summary": summary, "items": list_priority_queue(conn, {"icp_rule_id": rule["id"], "list_id": list_id}).get("items", [])}


def parse_priority_item_row(row):
    data = dict_row(row)
    if not data:
        return None
    data["reason"] = json.loads(data.pop("reason_json") or "{}")
    return data


def list_priority_queue(conn, params=None):
    params = params or {}
    where = ["q.org_id = ?"]
    values = [ORG_ID]
    if params.get("icp_rule_id"):
        where.append("q.icp_rule_id = ?")
        values.append(int(params.get("icp_rule_id")))
    if params.get("status"):
        where.append("q.status = ?")
        values.append(params.get("status"))
    if params.get("list_id"):
        where.append("q.list_id = ?")
        values.append(int(params.get("list_id")))
    rows = conn.execute(
        """
        SELECT q.*, r.name AS icp_name, l.email AS lead_email, c.cnpj,
               c.legal_name, c.trade_name, c.email AS company_email,
               c.city, c.state, c.main_cnae_code, c.size, c.opportunity_score
        FROM lead_priority_queue q
        JOIN icp_rules r ON r.id = q.icp_rule_id
        JOIN companies c ON c.id = q.company_id
        LEFT JOIN leads l ON l.id = q.lead_id
        WHERE %s
        ORDER BY q.priority_score DESC, q.id DESC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [min(int(params.get("limit", 100) or 100), 500)],
    ).fetchall()
    return {"items": [parse_priority_item_row(row) for row in rows]}


def decide_priority_queue_item(conn, item_id, decision, note=""):
    if decision not in ("accept", "reject"):
        raise ValueError("Decisao invalida")
    item = conn.execute(
        "SELECT * FROM lead_priority_queue WHERE id = ? AND org_id = ?",
        (item_id, ORG_ID),
    ).fetchone()
    if not item:
        raise ValueError("Sugestao nao encontrada")
    if item["status"] not in ("suggested", "stale"):
        raise ValueError("Sugestao ja decidida")
    status = "accepted" if decision == "accept" else "rejected"
    timestamp = now_iso()
    conn.execute(
        """
        UPDATE lead_priority_queue
        SET status = ?, decision_note = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, note or "", timestamp, item_id),
    )
    log_agent_action(
        conn,
        item["lead_id"],
        None,
        "priority_%s" % status,
        "human",
        note or ("Sugestao %s por humano" % status),
        {"priority_queue_id": item_id, "icp_rule_id": item["icp_rule_id"], "company_id": item["company_id"]},
    )
    audit(conn, "decide_priority_queue_item", "lead_priority_queue", item_id, {"status": status, "note": note})
    return parse_priority_item_row(
        conn.execute(
            """
            SELECT q.*, r.name AS icp_name, l.email AS lead_email, c.cnpj,
                   c.legal_name, c.trade_name, c.email AS company_email,
                   c.city, c.state, c.main_cnae_code, c.size, c.opportunity_score
            FROM lead_priority_queue q
            JOIN icp_rules r ON r.id = q.icp_rule_id
            JOIN companies c ON c.id = q.company_id
            LEFT JOIN leads l ON l.id = q.lead_id
            WHERE q.id = ?
            """,
            (item_id,),
        ).fetchone()
    )


REPLY_CLASSIFICATIONS = {
    "interest_meeting",
    "question",
    "not_interested",
    "opt_out",
    "out_of_office",
    "wrong_person",
    "ambiguous",
}

REPLY_HANDOFFS = {
    "opt_out": ("urgent", "Opt-out detectado; confirmar que nao havera novo contato"),
    "interest_meeting": ("high", "Lead demonstrou interesse ou pediu conversa"),
    "question": ("medium", "Lead fez pergunta ou pediu mais informacoes"),
    "wrong_person": ("medium", "Resposta indica pessoa errada ou redirecionamento"),
    "ambiguous": ("high", "Resposta ambigua exige julgamento humano"),
    "out_of_office": ("low", "Autoresposta ou ausencia temporaria"),
}

REPLY_LEAD_STATUS = {
    "opt_out": "opt_out",
    "interest_meeting": "responded",
    "question": "responded",
    "wrong_person": "responded",
    "ambiguous": "responded",
    "not_interested": "disqualified",
    "out_of_office": "waiting_reply_review",
}

REPLY_JOURNEY_STATUS = {
    "opt_out": "opt_out",
    "interest_meeting": "responded",
    "question": "responded",
    "wrong_person": "responded",
    "ambiguous": "responded",
    "not_interested": "disqualified",
    "out_of_office": "paused_reply",
}

ACTIVE_JOURNEY_STATUSES = {"pending_approval", "waiting"}


def ascii_lower(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


def contains_any(text, terms):
    return any(term in text for term in terms)


def classify_reply_text(subject="", body=""):
    text = ascii_lower("%s\n%s" % (subject or "", body or ""))
    compact = re.sub(r"\s+", " ", text).strip()
    reasons = []
    if contains_any(
        compact,
        [
            "remover",
            "descadastrar",
            "descadastro",
            "nao receber",
            "nao quero receber",
            "pare de enviar",
            "parar contato",
            "retirar meu email",
            "tire meu email",
            "unsubscribe",
            "opt out",
        ],
    ):
        reasons.append("Pedido de remocao ou descadastro detectado")
        return {"classification": "opt_out", "confidence": 0.98, "reasons": reasons}
    if contains_any(compact, ["fora do escritorio", "estou de ferias", "ausencia temporaria", "resposta automatica", "automatic reply", "out of office"]):
        reasons.append("Autoresposta ou ausencia detectada")
        return {"classification": "out_of_office", "confidence": 0.90, "reasons": reasons}
    if contains_any(compact, ["pessoa errada", "nao sou responsavel", "nao sou a pessoa", "fale com", "procure ", "responsavel e"]):
        reasons.append("Mensagem indica pessoa errada ou redirecionamento")
        return {"classification": "wrong_person", "confidence": 0.88, "reasons": reasons}
    if contains_any(compact, ["nao tenho interesse", "sem interesse", "nao faz sentido", "no momento nao", "nao obrigado", "dispenso"]):
        reasons.append("Recusa clara detectada")
        return {"classification": "not_interested", "confidence": 0.88, "reasons": reasons}
    if contains_any(
        compact,
        [
            "tenho interesse",
            "temos interesse",
            "vamos conversar",
            "podemos conversar",
            "marcar uma reuniao",
            "agendar",
            "me ligue",
            "pode me ligar",
            "quero conhecer",
            "mande horarios",
        ],
    ):
        reasons.append("Interesse ou pedido de conversa detectado")
        return {"classification": "interest_meeting", "confidence": 0.92, "reasons": reasons}
    if "?" in (subject or "") or "?" in (body or "") or contains_any(
        compact,
        ["como funciona", "quanto custa", "qual valor", "mais informacoes", "mais detalhes", "tenho uma duvida", "pode explicar"],
    ):
        reasons.append("Pergunta ou pedido de informacao detectado")
        return {"classification": "question", "confidence": 0.82, "reasons": reasons}
    reasons.append("Sem padrao confiavel; revisar manualmente")
    return {"classification": "ambiguous", "confidence": 0.45, "reasons": reasons}


def reply_target(conn, payload):
    send_id = int(payload.get("send_id") or 0)
    lead_id = int(payload.get("lead_id") or 0)
    email = normalize_email(payload.get("email") or "")
    target = {"send_id": None, "lead_id": None, "campaign_id": None, "email": email}
    if send_id:
        row = conn.execute(
            """
            SELECT s.id AS send_id, s.lead_id, s.campaign_id, s.email,
                   l.company_id, l.list_id, l.status AS lead_status
            FROM sends s
            JOIN leads l ON l.id = s.lead_id
            WHERE s.id = ?
            """,
            (send_id,),
        ).fetchone()
        if not row:
            raise ValueError("Envio nao encontrado")
        target.update(dict_row(row))
        target["email"] = normalize_email(row["email"])
        return target
    if lead_id:
        row = conn.execute(
            "SELECT id AS lead_id, company_id, list_id, email, status AS lead_status FROM leads WHERE id = ? AND org_id = ?",
            (lead_id, ORG_ID),
        ).fetchone()
        if not row:
            raise ValueError("Lead nao encontrado")
        target.update(dict_row(row))
        target["email"] = normalize_email(row["email"] or email)
        return target
    if email:
        row = conn.execute(
            """
            SELECT id AS lead_id, company_id, list_id, email, status AS lead_status
            FROM leads
            WHERE org_id = ? AND lower(email) = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (ORG_ID, email),
        ).fetchone()
        if row:
            target.update(dict_row(row))
            target["email"] = normalize_email(row["email"])
    return target


def add_opt_out(conn, email, reason, source="reply"):
    email = normalize_email(email)
    if not email:
        return
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO opt_outs (org_id, email, requested_by, reason, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET reason = excluded.reason
        """,
        (ORG_ID, email, source, reason, timestamp),
    )


def stop_journeys_for_reply(conn, lead_id, status, reason, timestamp):
    if not lead_id:
        return 0
    placeholders = ",".join("?" for _ in ACTIVE_JOURNEY_STATUSES)
    values = [status, reason, timestamp, int(lead_id), ORG_ID] + sorted(ACTIVE_JOURNEY_STATUSES)
    cursor = conn.execute(
        """
        UPDATE lead_journey
        SET status = ?, block_reason = ?, updated_at = ?
        WHERE lead_id = ? AND org_id = ? AND status IN (%s)
        """ % placeholders,
        values,
    )
    return cursor.rowcount


def register_reply_event(conn, target, classification, payload, timestamp):
    if not target.get("send_id"):
        return None
    event_payload = {
        "classification": classification,
        "subject": payload.get("subject") or "",
        "source": payload.get("source") or "manual_reply",
    }
    conn.execute(
        """
        INSERT INTO events (send_id, lead_id, campaign_id, event_type, source, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            target["send_id"],
            target.get("lead_id"),
            target.get("campaign_id"),
            "replied",
            payload.get("source") or "manual_reply",
            json.dumps(event_payload, ensure_ascii=True),
            timestamp,
        ),
    )
    conn.execute("UPDATE sends SET status = ? WHERE id = ?", ("replied", target["send_id"]))
    conn.execute(
        """
        INSERT INTO conversions (lead_id, campaign_id, conversion_type, utm_json, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            target.get("lead_id"),
            target.get("campaign_id"),
            "reply",
            json.dumps({}, ensure_ascii=True),
            "Classificacao: %s" % classification,
            timestamp,
        ),
    )


def create_handoff_for_reply(conn, target, reply_id, classification, reason, priority, payload, timestamp):
    context = {
        "reply_classification_id": reply_id,
        "classification": classification,
        "email": target.get("email") or normalize_email(payload.get("email") or ""),
        "subject": payload.get("subject") or "",
        "body_preview": (payload.get("body") or "")[:500],
        "send_id": target.get("send_id"),
        "campaign_id": target.get("campaign_id"),
    }
    cursor = conn.execute(
        """
        INSERT INTO handoffs (
            org_id, lead_id, reply_classification_id, status, priority,
            reason, context_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            target.get("lead_id"),
            reply_id,
            "pending",
            priority,
            reason,
            json.dumps(context, ensure_ascii=True),
            timestamp,
        ),
    )
    return cursor.lastrowid


def record_inbound_reply(conn, payload):
    subject = payload.get("subject") or ""
    body = payload.get("body") or payload.get("body_text") or ""
    if not body.strip() and not subject.strip():
        raise ValueError("Informe assunto ou corpo da resposta")
    target = reply_target(conn, payload)
    classification = classify_reply_text(subject, body)
    label = classification["classification"]
    if label not in REPLY_CLASSIFICATIONS:
        raise ValueError("Classificacao invalida")
    timestamp = now_iso()
    email = target.get("email") or normalize_email(payload.get("email") or "")
    cursor = conn.execute(
        """
        INSERT INTO reply_classifications (
            org_id, lead_id, send_id, email, subject, body_text, classification,
            confidence, reasons_json, raw_payload_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            target.get("lead_id"),
            target.get("send_id"),
            email,
            subject,
            body,
            label,
            float(classification["confidence"]),
            json.dumps(classification["reasons"], ensure_ascii=True),
            json.dumps(payload, ensure_ascii=True),
            timestamp,
        ),
    )
    reply_id = cursor.lastrowid
    lead_status = REPLY_LEAD_STATUS[label]
    journey_status = REPLY_JOURNEY_STATUS[label]
    if label == "opt_out":
        add_opt_out(conn, email, "Opt-out por resposta recebida", source="reply")
        add_suppression(conn, email, "opt_out_reply", source="reply")
    if target.get("lead_id"):
        conn.execute(
            "UPDATE leads SET status = ?, block_reason = ?, updated_at = ? WHERE id = ?",
            (
                lead_status,
                "Resposta classificada como %s" % label if label in ("opt_out", "not_interested") else "",
                timestamp,
                target["lead_id"],
            ),
        )
    stopped = stop_journeys_for_reply(conn, target.get("lead_id"), journey_status, "Resposta classificada como %s" % label, timestamp)
    register_reply_event(conn, target, label, payload, timestamp)
    handoff_id = None
    if label in REPLY_HANDOFFS:
        priority, reason = REPLY_HANDOFFS[label]
        handoff_id = create_handoff_for_reply(conn, target, reply_id, label, reason, priority, payload, timestamp)
    log_agent_action(
        conn,
        target.get("lead_id"),
        None,
        "reply_classified",
        "system",
        "Resposta classificada como %s" % label,
        {
            "reply_classification_id": reply_id,
            "classification": label,
            "confidence": classification["confidence"],
            "handoff_id": handoff_id,
            "journeys_stopped": stopped,
        },
    )
    if handoff_id:
        log_agent_action(
            conn,
            target.get("lead_id"),
            None,
            "handoff_created",
            "system",
            "Handoff criado para resposta %s" % label,
            {"reply_classification_id": reply_id, "handoff_id": handoff_id},
        )
    audit(
        conn,
        "record_inbound_reply",
        "reply_classification",
        reply_id,
        {"classification": label, "handoff_id": handoff_id, "journeys_stopped": stopped},
    )
    return {
        "reply": get_reply_classification(conn, reply_id),
        "handoff": get_handoff(conn, handoff_id) if handoff_id else None,
        "journeys_stopped": stopped,
    }


def parse_reply_row(row):
    data = dict_row(row)
    if not data:
        return None
    data["reasons"] = json.loads(data.pop("reasons_json") or "[]")
    data["raw_payload"] = json.loads(data.pop("raw_payload_json") or "{}")
    return data


def get_reply_classification(conn, reply_id):
    row = conn.execute(
        """
        SELECT rc.*, l.email AS lead_email, c.legal_name, c.trade_name
        FROM reply_classifications rc
        LEFT JOIN leads l ON l.id = rc.lead_id
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE rc.id = ? AND rc.org_id = ?
        """,
        (reply_id, ORG_ID),
    ).fetchone()
    return parse_reply_row(row)


def list_reply_classifications(conn, params=None):
    params = params or {}
    where = ["rc.org_id = ?"]
    values = [ORG_ID]
    if params.get("classification"):
        where.append("rc.classification = ?")
        values.append(params.get("classification"))
    rows = conn.execute(
        """
        SELECT rc.*, l.email AS lead_email, c.legal_name, c.trade_name
        FROM reply_classifications rc
        LEFT JOIN leads l ON l.id = rc.lead_id
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE %s
        ORDER BY rc.id DESC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [min(int(params.get("limit", 100) or 100), 500)],
    ).fetchall()
    return {"items": [parse_reply_row(row) for row in rows]}


def parse_handoff_row(row):
    data = dict_row(row)
    if not data:
        return None
    data["context"] = json.loads(data.pop("context_json") or "{}")
    return data


def get_handoff(conn, handoff_id):
    if not handoff_id:
        return None
    row = conn.execute(
        """
        SELECT h.*, l.email AS lead_email, c.legal_name, c.trade_name
        FROM handoffs h
        LEFT JOIN leads l ON l.id = h.lead_id
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE h.id = ? AND h.org_id = ?
        """,
        (handoff_id, ORG_ID),
    ).fetchone()
    return parse_handoff_row(row)


def list_handoffs(conn, params=None):
    params = params or {}
    where = ["h.org_id = ?"]
    values = [ORG_ID]
    if params.get("status"):
        where.append("h.status = ?")
        values.append(params.get("status"))
    else:
        where.append("h.status = 'pending'")
    rows = conn.execute(
        """
        SELECT h.*, l.email AS lead_email, c.legal_name, c.trade_name
        FROM handoffs h
        LEFT JOIN leads l ON l.id = h.lead_id
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE %s
        ORDER BY
          CASE h.priority
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            ELSE 4
          END,
          h.id DESC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [min(int(params.get("limit", 100) or 100), 500)],
    ).fetchall()
    return {"items": [parse_handoff_row(row) for row in rows]}


def decide_handoff(conn, handoff_id, decision, note=""):
    if decision not in ("resolve", "dismiss"):
        raise ValueError("Decisao de handoff invalida")
    handoff = conn.execute(
        "SELECT * FROM handoffs WHERE id = ? AND org_id = ?",
        (handoff_id, ORG_ID),
    ).fetchone()
    if not handoff:
        raise ValueError("Handoff nao encontrado")
    if handoff["status"] != "pending":
        raise ValueError("Handoff ja decidido")
    status = "resolved" if decision == "resolve" else "dismissed"
    timestamp = now_iso()
    conn.execute(
        "UPDATE handoffs SET status = ?, resolved_at = ?, resolution_note = ? WHERE id = ?",
        (status, timestamp, note or "", handoff_id),
    )
    log_agent_action(
        conn,
        handoff["lead_id"],
        None,
        "handoff_%s" % status,
        "human",
        note or "Handoff %s por humano" % status,
        {"handoff_id": handoff_id, "reply_classification_id": handoff["reply_classification_id"]},
    )
    audit(conn, "decide_handoff", "handoff", handoff_id, {"status": status, "note": note})
    return get_handoff(conn, handoff_id)


MEETING_STATUSES = {"proposed", "scheduled", "completed", "cancelled", "no_show"}
MEETING_LEAD_STATUS = {
    "proposed": "meeting_scheduled",
    "scheduled": "meeting_scheduled",
    "completed": "qualified",
    "cancelled": "meeting_review",
    "no_show": "meeting_review",
}


def parse_meeting_row(row):
    return dict_row(row)


def get_meeting(conn, meeting_id):
    row = conn.execute(
        """
        SELECT m.*, l.email AS lead_email, l.status AS lead_status,
               c.legal_name, c.trade_name, c.cnpj, c.city, c.state,
               rc.classification AS reply_classification,
               h.priority AS handoff_priority
        FROM meetings m
        JOIN leads l ON l.id = m.lead_id
        LEFT JOIN companies c ON c.id = m.company_id
        LEFT JOIN reply_classifications rc ON rc.id = m.reply_classification_id
        LEFT JOIN handoffs h ON h.id = m.handoff_id
        WHERE m.id = ? AND m.org_id = ?
        """,
        (meeting_id, ORG_ID),
    ).fetchone()
    return parse_meeting_row(row)


def meeting_lead(conn, lead_id):
    row = conn.execute(
        """
        SELECT l.*, c.legal_name, c.trade_name
        FROM leads l
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE l.id = ? AND l.org_id = ?
        """,
        (lead_id, ORG_ID),
    ).fetchone()
    if not row:
        raise ValueError("Lead nao encontrado")
    return dict_row(row)


def ensure_meeting_allowed(conn, lead):
    email = normalize_email(lead.get("email") or "")
    if not email:
        raise ValueError("Lead sem e-mail para reuniao")
    if lead.get("status") == "opt_out":
        raise ValueError("Lead em opt-out nao pode receber reuniao")
    suppression, opt_out = suppression_sets(conn)
    if email in suppression or email in opt_out:
        raise ValueError("E-mail suprimido ou em opt-out nao pode receber reuniao")


def meeting_status_from_payload(payload):
    status = (payload.get("status") or "").strip() or ("scheduled" if payload.get("scheduled_at") else "proposed")
    if status not in MEETING_STATUSES:
        raise ValueError("Status de reuniao invalido")
    return status


def meeting_duration(value):
    try:
        duration = int(value or 30)
    except (TypeError, ValueError):
        duration = 30
    return max(5, min(duration, 240))


def handoff_for_meeting(conn, handoff_id):
    row = conn.execute(
        """
        SELECT h.*, rc.classification
        FROM handoffs h
        LEFT JOIN reply_classifications rc ON rc.id = h.reply_classification_id
        WHERE h.id = ? AND h.org_id = ?
        """,
        (handoff_id, ORG_ID),
    ).fetchone()
    if not row:
        raise ValueError("Handoff nao encontrado")
    if row["status"] != "pending":
        raise ValueError("Handoff ja decidido")
    if not row["lead_id"]:
        raise ValueError("Handoff sem lead vinculado")
    return dict_row(row)


def create_meeting(conn, payload):
    payload = payload or {}
    handoff = None
    handoff_id = int(payload.get("handoff_id") or 0)
    lead_id = int(payload.get("lead_id") or 0)
    reply_id = int(payload.get("reply_classification_id") or 0) or None
    source = payload.get("source") or "manual"
    if handoff_id:
        handoff = handoff_for_meeting(conn, handoff_id)
        lead_id = int(handoff["lead_id"])
        reply_id = handoff["reply_classification_id"]
        source = "handoff"
    if not lead_id:
        raise ValueError("Informe lead_id ou handoff_id")

    lead = meeting_lead(conn, lead_id)
    ensure_meeting_allowed(conn, lead)
    status = meeting_status_from_payload(payload)
    timestamp = now_iso()
    company_name = lead.get("trade_name") or lead.get("legal_name") or "lead"
    title = (payload.get("title") or "Reuniao com %s" % company_name).strip()
    note = payload.get("notes") or payload.get("note") or ""
    cursor = conn.execute(
        """
        INSERT INTO meetings (
            org_id, lead_id, company_id, reply_classification_id, handoff_id, status,
            title, attendee_email, scheduled_at, duration_minutes, meeting_url,
            owner_name, notes, outcome_note, source, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            lead_id,
            lead.get("company_id"),
            reply_id,
            handoff_id or None,
            status,
            title,
            normalize_email(payload.get("attendee_email") or lead.get("email") or ""),
            payload.get("scheduled_at") or "",
            meeting_duration(payload.get("duration_minutes")),
            payload.get("meeting_url") or "",
            payload.get("owner_name") or "Operador interno",
            note,
            payload.get("outcome_note") or "",
            source,
            timestamp,
            timestamp,
        ),
    )
    meeting_id = cursor.lastrowid
    conn.execute(
        "UPDATE leads SET status = ?, block_reason = ?, updated_at = ? WHERE id = ?",
        (MEETING_LEAD_STATUS[status], "", timestamp, lead_id),
    )
    conn.execute(
        """
        INSERT INTO conversions (lead_id, campaign_id, conversion_type, utm_json, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (lead_id, None, "meeting_scheduled", json.dumps({}, ensure_ascii=True), note, timestamp),
    )
    if handoff:
        resolution_note = payload.get("resolution_note") or note or "Reuniao registrada a partir do handoff"
        conn.execute(
            "UPDATE handoffs SET status = ?, resolved_at = ?, resolution_note = ? WHERE id = ?",
            ("resolved", timestamp, resolution_note, handoff_id),
        )
        log_agent_action(
            conn,
            lead_id,
            None,
            "handoff_resolved",
            "human",
            resolution_note,
            {"handoff_id": handoff_id, "meeting_id": meeting_id},
        )
    log_agent_action(
        conn,
        lead_id,
        None,
        "meeting_created",
        "human",
        note or "Reuniao registrada",
        {"meeting_id": meeting_id, "handoff_id": handoff_id or None, "status": status},
    )
    audit(conn, "create_meeting", "meeting", meeting_id, {"handoff_id": handoff_id or None, "status": status})
    return get_meeting(conn, meeting_id)


def create_meeting_from_handoff(conn, handoff_id, payload):
    payload = dict(payload or {})
    payload["handoff_id"] = handoff_id
    return create_meeting(conn, payload)


def list_meetings(conn, params=None):
    params = params or {}
    where = ["m.org_id = ?"]
    values = [ORG_ID]
    if params.get("status"):
        where.append("m.status = ?")
        values.append(params.get("status"))
    if params.get("lead_id"):
        where.append("m.lead_id = ?")
        values.append(int(params.get("lead_id")))
    rows = conn.execute(
        """
        SELECT m.*, l.email AS lead_email, l.status AS lead_status,
               c.legal_name, c.trade_name, c.cnpj, c.city, c.state,
               rc.classification AS reply_classification,
               h.priority AS handoff_priority
        FROM meetings m
        JOIN leads l ON l.id = m.lead_id
        LEFT JOIN companies c ON c.id = m.company_id
        LEFT JOIN reply_classifications rc ON rc.id = m.reply_classification_id
        LEFT JOIN handoffs h ON h.id = m.handoff_id
        WHERE %s
        ORDER BY COALESCE(NULLIF(m.scheduled_at, ''), m.created_at) DESC, m.id DESC
        LIMIT ?
        """
        % " AND ".join(where),
        values + [min(int(params.get("limit", 100) or 100), 500)],
    ).fetchall()
    return {"items": [parse_meeting_row(row) for row in rows]}


def update_meeting_status(conn, meeting_id, status, note=""):
    status = (status or "").strip()
    if status not in MEETING_STATUSES:
        raise ValueError("Status de reuniao invalido")
    row = conn.execute(
        """
        SELECT m.*, l.email AS lead_email, l.status AS lead_status
        FROM meetings m
        JOIN leads l ON l.id = m.lead_id
        WHERE m.id = ? AND m.org_id = ?
        """,
        (meeting_id, ORG_ID),
    ).fetchone()
    if not row:
        raise ValueError("Reuniao nao encontrada")
    current = dict_row(row)
    if status in ("proposed", "scheduled"):
        ensure_meeting_allowed(conn, {"email": current["lead_email"], "status": current["lead_status"]})
    timestamp = now_iso()
    conn.execute(
        "UPDATE meetings SET status = ?, outcome_note = ?, updated_at = ? WHERE id = ?",
        (status, note or current.get("outcome_note") or "", timestamp, meeting_id),
    )
    conn.execute(
        "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
        (MEETING_LEAD_STATUS[status], timestamp, current["lead_id"]),
    )
    if status == "completed" and current["status"] != "completed":
        conn.execute(
            """
            INSERT INTO conversions (lead_id, campaign_id, conversion_type, utm_json, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (current["lead_id"], None, "meeting_completed", json.dumps({}, ensure_ascii=True), note or "", timestamp),
        )
    log_agent_action(
        conn,
        current["lead_id"],
        None,
        "meeting_status_updated",
        "human",
        note or "Status de reuniao atualizado para %s" % status,
        {"meeting_id": meeting_id, "from": current["status"], "to": status},
    )
    audit(conn, "update_meeting_status", "meeting", meeting_id, {"from": current["status"], "to": status})
    return get_meeting(conn, meeting_id)


COMMAND_CENTER_PRIORITY = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
COMMAND_CENTER_COLUMNS = [
    ("new", "Novos", {"new", "eligible"}),
    ("approval", "Aguardando humano", {"pending_approval"}),
    ("sequence", "Em cadencia", {"waiting", "in_campaign"}),
    ("reply", "Respondeu", {"responded", "waiting_reply_review", "meeting_review"}),
    ("meeting", "Reuniao", {"meeting_scheduled"}),
    ("qualified", "Qualificados", {"qualified", "converted"}),
    ("closed", "Encerrados", {"disqualified", "opt_out", "blocked"}),
]


def command_origin_label(source):
    labels = {
        "approval": "Regra de negocio / aprovacao humana",
        "handoff": "Sistema / handoff humano",
        "meeting": "Humano / agenda operacional",
        "system": "Regra de negocio",
        "human": "Humano",
        "agent": "Agente SDR",
        "manual": "Humano",
    }
    return labels.get(source or "", source or "Origem nao informada")


def timeline_json(value, fallback):
    try:
        return json.loads(value or "")
    except (TypeError, ValueError):
        return fallback


def add_timeline_item(items, occurred_at, source_table, source_id, kind, title, origin_label, detail, metadata=None):
    if not occurred_at:
        return
    items.append(
        {
            "occurred_at": occurred_at,
            "source_table": source_table,
            "source_id": source_id,
            "kind": kind,
            "title": title,
            "origin_label": origin_label,
            "detail": detail or "",
            "metadata": metadata or {},
        }
    )


def lead_timeline(conn, lead_id):
    lead_id = int(lead_id or 0)
    row = conn.execute(
        """
        SELECT l.*, c.id AS company_row_id, c.cnpj, c.legal_name, c.trade_name,
               c.city, c.state, c.main_cnae_code, c.main_cnae_description,
               c.email AS company_email, c.phone, c.sector,
               c.opportunity_score, c.source_name, c.legal_basis,
               c.collected_at
        FROM leads l
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE l.id = ? AND l.org_id = ?
        """,
        (lead_id, ORG_ID),
    ).fetchone()
    if not row:
        return None

    data = dict_row(row)
    lead = {
        "id": data["id"],
        "company_id": data.get("company_id"),
        "list_id": data.get("list_id"),
        "email": data.get("email") or "",
        "segment": data.get("segment") or "",
        "source": data.get("source") or "",
        "score": data.get("score") or 0,
        "status": data.get("status") or "",
        "block_reason": data.get("block_reason") or "",
        "created_at": data.get("created_at") or "",
        "updated_at": data.get("updated_at") or "",
    }
    company = None
    if data.get("company_row_id"):
        company = {
            "id": data.get("company_row_id"),
            "cnpj": data.get("cnpj") or "",
            "legal_name": data.get("legal_name") or "",
            "trade_name": data.get("trade_name") or "",
            "city": data.get("city") or "",
            "state": data.get("state") or "",
            "main_cnae_code": data.get("main_cnae_code") or "",
            "main_cnae_description": data.get("main_cnae_description") or "",
            "email": data.get("company_email") or "",
            "phone": data.get("phone") or "",
            "sector": data.get("sector") or "",
            "opportunity_score": data.get("opportunity_score") or 0,
            "source_name": data.get("source_name") or "",
            "legal_basis": data.get("legal_basis") or "",
            "collected_at": data.get("collected_at") or "",
        }

    items = []
    company_name = (company or {}).get("trade_name") or (company or {}).get("legal_name") or lead["email"]
    add_timeline_item(
        items,
        lead["created_at"],
        "leads",
        lead["id"],
        "lead",
        "Lead criado",
        "CRM interno",
        "Lead criado para %s com status %s" % (company_name or lead["email"], lead["status"]),
        {
            "email": lead["email"],
            "source": lead["source"],
            "score": lead["score"],
            "list_id": lead["list_id"],
        },
    )
    if lead["updated_at"] and lead["updated_at"] != lead["created_at"]:
        add_timeline_item(
            items,
            lead["updated_at"],
            "leads",
            lead["id"],
            "lead_status",
            "Status atual do lead",
            "CRM interno",
            lead["block_reason"] or "Lead esta em %s" % lead["status"],
            {"status": lead["status"], "block_reason": lead["block_reason"]},
        )

    priority_rows = conn.execute(
        """
        SELECT q.*, r.name AS icp_name
        FROM lead_priority_queue q
        JOIN icp_rules r ON r.id = q.icp_rule_id
        WHERE q.org_id = ? AND (q.lead_id = ? OR q.company_id = ?)
        ORDER BY q.id ASC
        """,
        (ORG_ID, lead_id, lead.get("company_id") or 0),
    ).fetchall()
    for priority in priority_rows:
        item = dict_row(priority)
        reason = timeline_json(item.get("reason_json"), {})
        add_timeline_item(
            items,
            item["created_at"],
            "lead_priority_queue",
            item["id"],
            "priority",
            "Lead priorizado por ICP",
            "Regra de negocio",
            "ICP %s sugeriu prioridade %s" % (item.get("icp_name") or item["icp_rule_id"], item["priority_score"]),
            {
                "status": item["status"],
                "fit_score": item["fit_score"],
                "priority_score": item["priority_score"],
                "reason": reason,
            },
        )
        if item.get("decision_note") or item.get("updated_at") != item.get("created_at"):
            add_timeline_item(
                items,
                item["updated_at"],
                "lead_priority_queue",
                item["id"],
                "priority_decision",
                "Decisao de prioridade",
                "Humano",
                item.get("decision_note") or "Prioridade atualizada para %s" % item["status"],
                {"status": item["status"], "decision_note": item.get("decision_note") or ""},
            )

    journey_rows = conn.execute(
        """
        SELECT lj.*, s.name AS sequence_name, ss.name AS step_name
        FROM lead_journey lj
        JOIN sequences s ON s.id = lj.sequence_id
        LEFT JOIN sequence_steps ss ON ss.id = lj.current_step_id
        WHERE lj.org_id = ? AND lj.lead_id = ?
        ORDER BY lj.id ASC
        """,
        (ORG_ID, lead_id),
    ).fetchall()
    journey_ids = []
    for journey in journey_rows:
        item = dict_row(journey)
        journey_ids.append(item["id"])
        detail = "Sequencia %s, passo %s, status %s" % (
            item.get("sequence_name") or item["sequence_id"],
            item.get("current_step_number") or "-",
            item.get("status") or "-",
        )
        add_timeline_item(
            items,
            item["created_at"],
            "lead_journey",
            item["id"],
            "journey",
            "Jornada criada",
            "CRM interno",
            detail,
            {
                "sequence_id": item["sequence_id"],
                "sequence_name": item.get("sequence_name") or "",
                "current_step_id": item.get("current_step_id"),
                "current_step_number": item.get("current_step_number"),
                "next_action_at": item.get("next_action_at") or "",
            },
        )
        if item.get("updated_at") and item.get("updated_at") != item.get("created_at"):
            add_timeline_item(
                items,
                item["updated_at"],
                "lead_journey",
                item["id"],
                "journey_status",
                "Jornada atualizada",
                "CRM interno",
                item.get("block_reason") or "Jornada esta em %s" % item.get("status"),
                {
                    "status": item.get("status"),
                    "last_action_at": item.get("last_action_at") or "",
                    "next_action_at": item.get("next_action_at") or "",
                },
            )

    approval_rows = conn.execute(
        "SELECT * FROM approval_queue WHERE org_id = ? ORDER BY id ASC",
        (ORG_ID,),
    ).fetchall()
    for approval in approval_rows:
        item = dict_row(approval)
        context = timeline_json(item.get("context_json"), {})
        if int(context.get("lead_id") or 0) != lead_id and int(context.get("journey_id") or 0) not in journey_ids:
            continue
        add_timeline_item(
            items,
            item["created_at"],
            "approval_queue",
            item["id"],
            "approval",
            item["title"],
            command_origin_label("approval"),
            "Aprovacao criada com status %s" % item["status"],
            {"status": item["status"], "context": context},
        )
        if item.get("decided_at"):
            add_timeline_item(
                items,
                item["decided_at"],
                "approval_queue",
                item["id"],
                "approval_decision",
                "Decisao de aprovacao",
                "Humano",
                item.get("decision_note") or "Aprovacao %s" % item["status"],
                {"status": item["status"], "decision_note": item.get("decision_note") or ""},
            )

    send_rows = conn.execute(
        """
        SELECT s.*, c.name AS campaign_name, v.name AS variant_name
        FROM sends s
        JOIN campaigns c ON c.id = s.campaign_id
        JOIN campaign_variants v ON v.id = s.variant_id
        WHERE s.lead_id = ?
        ORDER BY s.id ASC
        """,
        (lead_id,),
    ).fetchall()
    for send in send_rows:
        item = dict_row(send)
        add_timeline_item(
            items,
            item["created_at"],
            "sends",
            item["id"],
            "send",
            "Envio registrado",
            command_origin_label("system"),
            "Campanha %s registrou envio %s" % (item.get("campaign_name") or item["campaign_id"], item["status"]),
            {
                "campaign_id": item["campaign_id"],
                "campaign_name": item.get("campaign_name") or "",
                "variant_id": item["variant_id"],
                "variant_name": item.get("variant_name") or "",
                "email": item["email"],
                "status": item["status"],
                "provider": item["provider"],
                "scheduled_at": item.get("scheduled_at") or "",
                "sent_at": item.get("sent_at") or "",
                "utm_url": item.get("utm_url") or "",
            },
        )
        if item.get("sent_at") and item.get("sent_at") != item.get("created_at"):
            add_timeline_item(
                items,
                item["sent_at"],
                "sends",
                item["id"],
                "send_sent",
                "Envio simulado executado",
                command_origin_label("system"),
                "Mensagem marcada como enviada para %s" % item["email"],
                {"provider_message_id": item.get("provider_message_id") or "", "provider": item["provider"]},
            )

    event_rows = conn.execute(
        """
        SELECT e.*, c.name AS campaign_name
        FROM events e
        LEFT JOIN campaigns c ON c.id = e.campaign_id
        WHERE e.lead_id = ?
        ORDER BY e.id ASC
        """,
        (lead_id,),
    ).fetchall()
    for event in event_rows:
        item = dict_row(event)
        payload = timeline_json(item.get("payload_json"), {})
        add_timeline_item(
            items,
            item["created_at"],
            "events",
            item["id"],
            "event",
            "Evento de campanha: %s" % item["event_type"],
            "Evento de campanha",
            "Evento %s via %s" % (item["event_type"], item["source"]),
            {
                "send_id": item.get("send_id"),
                "campaign_id": item.get("campaign_id"),
                "campaign_name": item.get("campaign_name") or "",
                "payload": payload,
            },
        )

    reply_rows = conn.execute(
        "SELECT * FROM reply_classifications WHERE org_id = ? AND lead_id = ? ORDER BY id ASC",
        (ORG_ID, lead_id),
    ).fetchall()
    for reply in reply_rows:
        item = dict_row(reply)
        reasons = timeline_json(item.get("reasons_json"), [])
        raw_payload = timeline_json(item.get("raw_payload_json"), {})
        add_timeline_item(
            items,
            item["created_at"],
            "reply_classifications",
            item["id"],
            "reply",
            "Resposta classificada",
            command_origin_label("system"),
            "Resposta classificada como %s" % item["classification"],
            {
                "send_id": item.get("send_id"),
                "email": item["email"],
                "subject": item.get("subject") or "",
                "confidence": item.get("confidence") or 0,
                "reasons": reasons,
                "raw_payload": raw_payload,
            },
        )

    handoff_rows = conn.execute(
        "SELECT * FROM handoffs WHERE org_id = ? AND lead_id = ? ORDER BY id ASC",
        (ORG_ID, lead_id),
    ).fetchall()
    for handoff in handoff_rows:
        item = dict_row(handoff)
        context = timeline_json(item.get("context_json"), {})
        add_timeline_item(
            items,
            item["created_at"],
            "handoffs",
            item["id"],
            "handoff",
            "Handoff humano criado",
            command_origin_label("handoff"),
            item["reason"],
            {
                "status": item["status"],
                "priority": item["priority"],
                "reply_classification_id": item.get("reply_classification_id"),
                "context": context,
            },
        )
        if item.get("resolved_at"):
            add_timeline_item(
                items,
                item["resolved_at"],
                "handoffs",
                item["id"],
                "handoff_decision",
                "Handoff decidido",
                "Humano",
                item.get("resolution_note") or "Handoff %s" % item["status"],
                {"status": item["status"], "resolution_note": item.get("resolution_note") or ""},
            )

    meeting_rows = conn.execute(
        "SELECT * FROM meetings WHERE org_id = ? AND lead_id = ? ORDER BY id ASC",
        (ORG_ID, lead_id),
    ).fetchall()
    for meeting in meeting_rows:
        item = dict_row(meeting)
        add_timeline_item(
            items,
            item["created_at"],
            "meetings",
            item["id"],
            "meeting",
            "Reuniao registrada",
            command_origin_label("meeting"),
            item.get("notes") or item["title"],
            {
                "status": item["status"],
                "scheduled_at": item.get("scheduled_at") or "",
                "meeting_url": item.get("meeting_url") or "",
                "owner_name": item.get("owner_name") or "",
                "handoff_id": item.get("handoff_id"),
                "reply_classification_id": item.get("reply_classification_id"),
            },
        )
        if item.get("updated_at") and (
            item.get("updated_at") != item.get("created_at") or item.get("status") in ("completed", "cancelled", "no_show")
        ):
            add_timeline_item(
                items,
                item["updated_at"],
                "meetings",
                item["id"],
                "meeting_status",
                "Status de reuniao",
                "Humano",
                item.get("outcome_note") or "Reuniao atualizada para %s" % item["status"],
                {"status": item["status"], "outcome_note": item.get("outcome_note") or ""},
            )

    conversion_rows = conn.execute(
        """
        SELECT cv.*, c.name AS campaign_name
        FROM conversions cv
        LEFT JOIN campaigns c ON c.id = cv.campaign_id
        WHERE cv.lead_id = ?
        ORDER BY cv.id ASC
        """,
        (lead_id,),
    ).fetchall()
    for conversion in conversion_rows:
        item = dict_row(conversion)
        add_timeline_item(
            items,
            item["created_at"],
            "conversions",
            item["id"],
            "conversion",
            "Conversao: %s" % item["conversion_type"],
            "Regra de negocio",
            item.get("notes") or "Conversao registrada",
            {
                "campaign_id": item.get("campaign_id"),
                "campaign_name": item.get("campaign_name") or "",
                "utm": timeline_json(item.get("utm_json"), {}),
            },
        )

    action_rows = conn.execute(
        """
        SELECT aa.*, s.name AS sequence_name
        FROM agent_actions aa
        LEFT JOIN sequences s ON s.id = aa.sequence_id
        WHERE aa.org_id = ? AND aa.lead_id = ?
        ORDER BY aa.id ASC
        """,
        (ORG_ID, lead_id),
    ).fetchall()
    for action in action_rows:
        item = dict_row(action)
        add_timeline_item(
            items,
            item["created_at"],
            "agent_actions",
            item["id"],
            "agent_action",
            item["action_type"],
            command_origin_label(item["source"]),
            item["reason"],
            {
                "source": item["source"],
                "sequence_id": item.get("sequence_id"),
                "sequence_name": item.get("sequence_name") or "",
                "payload": timeline_json(item.get("payload_json"), {}),
            },
        )

    kind_order = {
        "lead": 10,
        "lead_status": 11,
        "priority": 20,
        "priority_decision": 21,
        "journey": 30,
        "journey_status": 31,
        "approval": 40,
        "approval_decision": 41,
        "send": 50,
        "send_sent": 51,
        "event": 60,
        "reply": 70,
        "handoff": 80,
        "handoff_decision": 81,
        "meeting": 90,
        "meeting_status": 91,
        "conversion": 100,
        "agent_action": 110,
    }
    items.sort(key=lambda item: (item["occurred_at"], kind_order.get(item["kind"], 999), item["source_table"], item["source_id"]))
    for index, item in enumerate(items, start=1):
        item["sequence"] = index

    def count_kind(*kinds):
        return sum(1 for item in items if item["kind"] in kinds)

    return {
        "lead": lead,
        "company": company,
        "summary": {
            "timeline_items": len(items),
            "priority_items": count_kind("priority", "priority_decision"),
            "journeys": count_kind("journey", "journey_status"),
            "actions": count_kind("agent_action"),
            "approvals": count_kind("approval", "approval_decision"),
            "sends": count_kind("send", "send_sent"),
            "events": count_kind("event"),
            "replies": count_kind("reply"),
            "handoffs": count_kind("handoff", "handoff_decision"),
            "meetings": count_kind("meeting", "meeting_status"),
            "conversions": count_kind("conversion"),
        },
        "timeline": items,
    }


DEFAULT_KPIS = [
    {
        "kpi_key": "active_leads",
        "name": "Leads ativos",
        "description": "Leads que ainda nao estao encerrados, bloqueados ou em opt-out.",
        "formula": "COUNT(leads) WHERE status NOT IN ('disqualified','opt_out','blocked')",
        "unit": "count",
        "direction": "increase",
        "source_tables": ["leads"],
    },
    {
        "kpi_key": "simulated_sends",
        "name": "Envios simulados",
        "description": "Passos aprovados que criaram envio simulado.",
        "formula": "COUNT(sends) WHERE status = 'sent'",
        "unit": "count",
        "direction": "increase",
        "source_tables": ["sends"],
    },
    {
        "kpi_key": "replies_received",
        "name": "Respostas recebidas",
        "description": "Respostas classificadas no funil.",
        "formula": "COUNT(reply_classifications)",
        "unit": "count",
        "direction": "increase",
        "source_tables": ["reply_classifications"],
    },
    {
        "kpi_key": "pending_handoffs",
        "name": "Handoffs pendentes",
        "description": "Itens que ainda exigem decisao humana.",
        "formula": "COUNT(handoffs) WHERE status = 'pending'",
        "unit": "count",
        "direction": "decrease",
        "source_tables": ["handoffs"],
    },
    {
        "kpi_key": "open_meetings",
        "name": "Reunioes abertas",
        "description": "Reunioes propostas ou agendadas.",
        "formula": "COUNT(meetings) WHERE status IN ('proposed','scheduled')",
        "unit": "count",
        "direction": "increase",
        "source_tables": ["meetings"],
    },
    {
        "kpi_key": "meetings_completed",
        "name": "Reunioes concluidas",
        "description": "Reunioes marcadas como concluidas.",
        "formula": "COUNT(meetings) WHERE status = 'completed'",
        "unit": "count",
        "direction": "increase",
        "source_tables": ["meetings"],
    },
    {
        "kpi_key": "conversions_registered",
        "name": "Conversoes registradas",
        "description": "Conversoes de negocio registradas no funil.",
        "formula": "COUNT(conversions)",
        "unit": "count",
        "direction": "increase",
        "source_tables": ["conversions"],
    },
]


def ensure_default_kpis(conn):
    timestamp = now_iso()
    for kpi in DEFAULT_KPIS:
        conn.execute(
            """
            INSERT INTO kpi_definitions (
                org_id, kpi_key, name, description, formula, unit, direction,
                source_tables_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(org_id, kpi_key) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                formula = excluded.formula,
                unit = excluded.unit,
                direction = excluded.direction,
                source_tables_json = excluded.source_tables_json,
                updated_at = excluded.updated_at
            """,
            (
                ORG_ID,
                kpi["kpi_key"],
                kpi["name"],
                kpi["description"],
                kpi["formula"],
                kpi["unit"],
                kpi["direction"],
                json.dumps(kpi["source_tables"], ensure_ascii=True),
                timestamp,
                timestamp,
            ),
        )


def kpi_value(conn, kpi_key):
    queries = {
        "active_leads": (
            """
            SELECT COUNT(*) AS value
            FROM leads
            WHERE org_id = ? AND status NOT IN ('disqualified', 'opt_out', 'blocked')
            """,
            (ORG_ID,),
        ),
        "simulated_sends": (
            "SELECT COUNT(*) AS value FROM sends WHERE status = 'sent'",
            (),
        ),
        "replies_received": (
            "SELECT COUNT(*) AS value FROM reply_classifications WHERE org_id = ?",
            (ORG_ID,),
        ),
        "pending_handoffs": (
            "SELECT COUNT(*) AS value FROM handoffs WHERE org_id = ? AND status = 'pending'",
            (ORG_ID,),
        ),
        "open_meetings": (
            "SELECT COUNT(*) AS value FROM meetings WHERE org_id = ? AND status IN ('proposed', 'scheduled')",
            (ORG_ID,),
        ),
        "meetings_completed": (
            "SELECT COUNT(*) AS value FROM meetings WHERE org_id = ? AND status = 'completed'",
            (ORG_ID,),
        ),
        "conversions_registered": (
            "SELECT COUNT(*) AS value FROM conversions",
            (),
        ),
    }
    if kpi_key not in queries:
        raise ValueError("KPI desconhecido")
    sql, values = queries[kpi_key]
    return int(conn.execute(sql, values).fetchone()["value"] or 0)


def parse_kpi_row(conn, row):
    data = dict_row(row)
    data["source_tables"] = json.loads(data.pop("source_tables_json") or "[]")
    data["current_value"] = kpi_value(conn, data["kpi_key"])
    return data


def list_kpis(conn):
    ensure_default_kpis(conn)
    rows = conn.execute(
        """
        SELECT *
        FROM kpi_definitions
        WHERE org_id = ?
        ORDER BY id ASC
        """,
        (ORG_ID,),
    ).fetchall()
    return [parse_kpi_row(conn, row) for row in rows]


def kr_progress(current_value, target_value):
    try:
        target = float(target_value)
        current = float(current_value)
    except (TypeError, ValueError):
        return 0
    if target <= 0:
        return 0
    return int(min(100, round((current / target) * 100)))


def parse_key_result(conn, row, kpi_by_key):
    data = dict_row(row)
    kpi = kpi_by_key.get(data["kpi_key"])
    current = kpi["current_value"] if kpi else 0
    data["current_value"] = current
    data["progress"] = kr_progress(current, data["target_value"])
    data["kpi"] = kpi
    return data


def default_objective(kpi_by_key):
    defaults = [
        ("Gerar 20 respostas recebidas", "replies_received", 20),
        ("Concluir 5 reunioes", "meetings_completed", 5),
        ("Registrar 3 conversoes", "conversions_registered", 3),
    ]
    key_results = []
    for index, (title, kpi_key, target) in enumerate(defaults, start=1):
        kpi = kpi_by_key[kpi_key]
        current = kpi["current_value"]
        key_results.append(
            {
                "id": "default-%s" % index,
                "title": title,
                "kpi_key": kpi_key,
                "target_value": target,
                "current_value": current,
                "progress": kr_progress(current, target),
                "kpi": kpi,
            }
        )
    return {
        "id": "default",
        "title": "Validar outbound B2B com operacao auditavel",
        "description": "OKR default sintetico enquanto nenhum objetivo foi salvo.",
        "status": "template",
        "period_start": "",
        "period_end": "",
        "key_results": key_results,
    }


def list_objectives(conn, kpis):
    kpi_by_key = {item["kpi_key"]: item for item in kpis}
    objectives = conn.execute(
        """
        SELECT *
        FROM objectives
        WHERE org_id = ?
        ORDER BY id DESC
        """,
        (ORG_ID,),
    ).fetchall()
    if not objectives:
        return [default_objective(kpi_by_key)]

    result = []
    for objective in objectives:
        data = dict_row(objective)
        rows = conn.execute(
            """
            SELECT *
            FROM key_results
            WHERE objective_id = ?
            ORDER BY id ASC
            """,
            (data["id"],),
        ).fetchall()
        data["key_results"] = [parse_key_result(conn, row, kpi_by_key) for row in rows]
        result.append(data)
    return result


def okr_dashboard(conn):
    kpis = list_kpis(conn)
    return {
        "kpis": kpis,
        "objectives": list_objectives(conn, kpis),
    }


def create_okr(conn, payload):
    ensure_default_kpis(conn)
    payload = payload or {}
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("Titulo do objetivo e obrigatorio")
    key_results = payload.get("key_results") or []
    if not key_results:
        raise ValueError("Informe ao menos um key result")
    kpi_keys = {row["kpi_key"] for row in list_kpis(conn)}
    prepared_key_results = []
    for item in key_results:
        kpi_key = (item.get("kpi_key") or "").strip()
        if kpi_key not in kpi_keys:
            raise ValueError("KPI desconhecido: %s" % kpi_key)
        target_value = float(item.get("target_value") or 0)
        if target_value <= 0:
            raise ValueError("Meta do key result deve ser maior que zero")
        kr_title = (item.get("title") or "").strip() or "KR %s" % kpi_key
        prepared_key_results.append((kr_title, kpi_key, target_value))
    timestamp = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO objectives (
            org_id, title, description, status, period_start, period_end, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ORG_ID,
            title,
            payload.get("description") or "",
            payload.get("status") or "active",
            payload.get("period_start") or "",
            payload.get("period_end") or "",
            timestamp,
            timestamp,
        ),
    )
    objective_id = cursor.lastrowid
    for kr_title, kpi_key, target_value in prepared_key_results:
        conn.execute(
            """
            INSERT INTO key_results (
                objective_id, title, kpi_key, target_value, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (objective_id, kr_title, kpi_key, target_value, timestamp, timestamp),
        )
    audit(conn, "create_okr", "objective", objective_id, {"key_results": len(key_results)})
    return next(item for item in list_objectives(conn, list_kpis(conn)) if item["id"] == objective_id)


def command_center_metrics(conn):
    pending_approvals = conn.execute(
        "SELECT COUNT(*) AS total FROM approval_queue WHERE org_id = ? AND status = 'pending'",
        (ORG_ID,),
    ).fetchone()["total"]
    pending_handoffs = conn.execute(
        "SELECT COUNT(*) AS total FROM handoffs WHERE org_id = ? AND status = 'pending'",
        (ORG_ID,),
    ).fetchone()["total"]
    open_meetings = conn.execute(
        "SELECT COUNT(*) AS total FROM meetings WHERE org_id = ? AND status IN ('proposed', 'scheduled')",
        (ORG_ID,),
    ).fetchone()["total"]
    active_leads = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM leads
        WHERE org_id = ?
          AND status NOT IN ('disqualified', 'opt_out', 'blocked')
        """,
        (ORG_ID,),
    ).fetchone()["total"]
    recent_actions = conn.execute(
        "SELECT COUNT(*) AS total FROM agent_actions WHERE org_id = ?",
        (ORG_ID,),
    ).fetchone()["total"]
    return {
        "pending_approvals": int(pending_approvals or 0),
        "pending_handoffs": int(pending_handoffs or 0),
        "open_meetings": int(open_meetings or 0),
        "active_leads": int(active_leads or 0),
        "recent_actions": int(recent_actions or 0),
    }


def command_center_inbox(conn, limit=50):
    items = []
    for approval in list_approvals(conn, {"status": "pending", "limit": limit})["items"]:
        context = approval.get("context") or {}
        items.append(
            {
                "source_type": "approval",
                "source_id": approval["id"],
                "priority": "medium",
                "title": approval["title"],
                "company_name": context.get("company_name") or "",
                "email": context.get("email") or "",
                "status": approval["status"],
                "reason": "Passo de sequencia aguarda aprovacao humana",
                "origin_label": command_origin_label("approval"),
                "created_at": approval["created_at"],
                "context": context,
                "actions": [
                    {"decision": "approve", "label": "Aprovar"},
                    {"decision": "reject", "label": "Rejeitar"},
                ],
            }
        )
    for handoff in list_handoffs(conn, {"status": "pending", "limit": limit})["items"]:
        context = handoff.get("context") or {}
        items.append(
            {
                "source_type": "handoff",
                "source_id": handoff["id"],
                "priority": handoff["priority"],
                "title": handoff["reason"],
                "company_name": handoff.get("trade_name") or handoff.get("legal_name") or "",
                "email": handoff.get("lead_email") or context.get("email") or "",
                "status": handoff["status"],
                "reason": handoff["reason"],
                "origin_label": command_origin_label("handoff"),
                "created_at": handoff["created_at"],
                "context": context,
                "actions": [
                    {"decision": "resolve", "label": "Resolver"},
                    {"decision": "dismiss", "label": "Dispensar"},
                ],
            }
        )
    meeting_rows = conn.execute(
        """
        SELECT m.*, l.email AS lead_email, c.legal_name, c.trade_name
        FROM meetings m
        JOIN leads l ON l.id = m.lead_id
        LEFT JOIN companies c ON c.id = m.company_id
        WHERE m.org_id = ? AND m.status IN ('proposed', 'scheduled')
        ORDER BY COALESCE(NULLIF(m.scheduled_at, ''), m.created_at) ASC, m.id ASC
        LIMIT ?
        """,
        (ORG_ID, min(int(limit), 500)),
    ).fetchall()
    for row in meeting_rows:
        meeting = dict_row(row)
        items.append(
            {
                "source_type": "meeting",
                "source_id": meeting["id"],
                "priority": "high" if meeting["status"] == "scheduled" else "medium",
                "title": meeting["title"],
                "company_name": meeting.get("trade_name") or meeting.get("legal_name") or "",
                "email": meeting.get("attendee_email") or meeting.get("lead_email") or "",
                "status": meeting["status"],
                "reason": meeting.get("notes") or "Reuniao aberta para acompanhamento",
                "origin_label": command_origin_label("meeting"),
                "created_at": meeting["created_at"],
                "context": {
                    "lead_id": meeting["lead_id"],
                    "scheduled_at": meeting.get("scheduled_at") or "",
                    "meeting_url": meeting.get("meeting_url") or "",
                    "handoff_id": meeting.get("handoff_id"),
                },
                "actions": [
                    {"decision": "complete", "label": "Concluir"},
                    {"decision": "cancel", "label": "Cancelar"},
                    {"decision": "no_show", "label": "No-show"},
                ],
            }
        )
    items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    items.sort(key=lambda item: COMMAND_CENTER_PRIORITY.get(item.get("priority"), 9))
    return {"items": items[:limit]}


def lead_command_status(lead_status, journey_status):
    if journey_status in ("pending_approval", "waiting") and lead_status not in ("responded", "meeting_scheduled", "qualified", "disqualified", "opt_out", "blocked"):
        return journey_status
    return lead_status or "new"


def command_column_key(status):
    for key, _label, statuses in COMMAND_CENTER_COLUMNS:
        if status in statuses:
            return key
    return "reply"


def command_center_kanban(conn, limit=200):
    rows = conn.execute(
        """
        SELECT l.id, l.email, l.score, l.status AS lead_status, l.updated_at,
               c.legal_name, c.trade_name, c.city, c.state,
               lj.status AS journey_status, lj.next_action_at,
               s.name AS sequence_name
        FROM leads l
        LEFT JOIN companies c ON c.id = l.company_id
        LEFT JOIN lead_journey lj ON lj.id = (
            SELECT latest.id
            FROM lead_journey latest
            WHERE latest.lead_id = l.id AND latest.org_id = l.org_id
            ORDER BY latest.id DESC
            LIMIT 1
        )
        LEFT JOIN sequences s ON s.id = lj.sequence_id
        WHERE l.org_id = ?
        ORDER BY l.updated_at DESC, l.id DESC
        LIMIT ?
        """,
        (ORG_ID, min(int(limit), 500)),
    ).fetchall()
    columns = [{"key": key, "label": label, "items": []} for key, label, _statuses in COMMAND_CENTER_COLUMNS]
    by_key = {column["key"]: column for column in columns}
    for row in rows:
        lead = dict_row(row)
        status = lead_command_status(lead.get("lead_status"), lead.get("journey_status"))
        item = {
            "lead_id": lead["id"],
            "company_name": lead.get("trade_name") or lead.get("legal_name") or lead.get("email") or "",
            "email": lead.get("email") or "",
            "status": status,
            "lead_status": lead.get("lead_status") or "",
            "journey_status": lead.get("journey_status") or "",
            "score": lead.get("score") or 0,
            "city": lead.get("city") or "",
            "state": lead.get("state") or "",
            "next_action_at": lead.get("next_action_at") or "",
            "sequence_name": lead.get("sequence_name") or "",
            "origin_label": "CRM interno",
        }
        by_key[command_column_key(status)]["items"].append(item)
    return {"columns": columns}


def command_center_activity(conn, limit=100):
    rows = conn.execute(
        """
        SELECT aa.*, l.email AS lead_email, c.legal_name, c.trade_name
        FROM agent_actions aa
        LEFT JOIN leads l ON l.id = aa.lead_id
        LEFT JOIN companies c ON c.id = l.company_id
        WHERE aa.org_id = ?
        ORDER BY aa.id DESC
        LIMIT ?
        """,
        (ORG_ID, min(int(limit), 500)),
    ).fetchall()
    items = []
    for row in rows:
        action = dict_row(row)
        items.append(
            {
                "id": action["id"],
                "action_type": action["action_type"],
                "source": action["source"],
                "origin_label": command_origin_label(action["source"]),
                "reason": action["reason"],
                "lead_email": action.get("lead_email") or "",
                "company_name": action.get("trade_name") or action.get("legal_name") or "",
                "created_at": action["created_at"],
                "payload": json.loads(action.pop("payload_json") or "{}"),
            }
        )
    return {"items": items}


def command_center(conn):
    return {
        "metrics": command_center_metrics(conn),
        "inbox": command_center_inbox(conn, 50),
        "kanban": command_center_kanban(conn, 200),
        "activity": command_center_activity(conn, 100),
    }


def command_center_action(conn, payload):
    payload = payload or {}
    source_type = (payload.get("source_type") or "").strip()
    decision = (payload.get("decision") or "").strip()
    source_id = int(payload.get("source_id") or 0)
    note = payload.get("note") or ""
    if not source_id:
        raise ValueError("Informe source_id")

    if source_type == "approval":
        if decision == "approve":
            result = approve_sequence_step(conn, source_id, note)
        elif decision == "reject":
            result = reject_sequence_step(conn, source_id, note)
        else:
            raise ValueError("Decisao invalida para approval")
    elif source_type == "handoff":
        if decision == "resolve":
            result = decide_handoff(conn, source_id, "resolve", note)
        elif decision == "dismiss":
            result = decide_handoff(conn, source_id, "dismiss", note)
        else:
            raise ValueError("Decisao invalida para handoff")
    elif source_type == "meeting":
        if decision == "complete":
            result = update_meeting_status(conn, source_id, "completed", note)
        elif decision == "cancel":
            result = update_meeting_status(conn, source_id, "cancelled", note)
        elif decision == "no_show":
            result = update_meeting_status(conn, source_id, "no_show", note)
        else:
            raise ValueError("Decisao invalida para meeting")
    else:
        raise ValueError("Tipo de origem invalido")

    return {
        "source_type": source_type,
        "source_id": source_id,
        "decision": decision,
        "result": result,
        "command_center": command_center(conn),
    }


def audit_events(conn, limit=100):
    rows = conn.execute(
        "SELECT * FROM audit_logs WHERE org_id = ? ORDER BY id DESC LIMIT ?",
        (ORG_ID, min(int(limit), 500)),
    ).fetchall()
    return [dict_row(row) for row in rows]
