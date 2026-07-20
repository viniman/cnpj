import csv
import io
import json
import os
import re
from datetime import datetime

from .database import now_iso
from .email_hygiene import classify_email, normalize_email
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


def audit_events(conn, limit=100):
    rows = conn.execute(
        "SELECT * FROM audit_logs WHERE org_id = ? ORDER BY id DESC LIMIT ?",
        (ORG_ID, min(int(limit), 500)),
    ).fetchall()
    return [dict_row(row) for row in rows]
