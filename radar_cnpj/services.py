import csv
import io
import json
import os
import re
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


def audit_events(conn, limit=100):
    rows = conn.execute(
        "SELECT * FROM audit_logs WHERE org_id = ? ORDER BY id DESC LIMIT ?",
        (ORG_ID, min(int(limit), 500)),
    ).fetchall()
    return [dict_row(row) for row in rows]
