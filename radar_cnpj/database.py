import os
import sqlite3
from datetime import datetime


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "radar_cnpj.sqlite")


def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def get_db_path():
    return os.environ.get("RADAR_CNPJ_DB", DEFAULT_DB_PATH)


def ensure_data_dir():
    os.makedirs(os.path.dirname(get_db_path()), exist_ok=True)


def connect():
    ensure_data_dir()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    ensure_data_dir()
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT 'admin',
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj TEXT NOT NULL UNIQUE,
                cnpj_root TEXT NOT NULL,
                legal_name TEXT NOT NULL,
                trade_name TEXT,
                status TEXT,
                opening_date TEXT,
                status_date TEXT,
                main_cnae_code TEXT,
                main_cnae_description TEXT,
                secondary_cnaes TEXT,
                legal_nature TEXT,
                size TEXT,
                establishment_type TEXT,
                street_type TEXT,
                street TEXT,
                number TEXT,
                complement TEXT,
                district TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                email TEXT,
                phone TEXT,
                capital_social REAL DEFAULT 0,
                sector TEXT,
                segment TEXT,
                market_value_estimate REAL DEFAULT 0,
                opportunity_score INTEGER DEFAULT 0,
                score_reasons TEXT,
                source_name TEXT NOT NULL,
                source_url TEXT,
                collected_at TEXT NOT NULL,
                legal_basis TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                qualification TEXT,
                entry_date TEXT,
                age_range TEXT,
                document_masked TEXT,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cnaes (
                code TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                sector TEXT
            );

            CREATE TABLE IF NOT EXISTS company_cnaes (
                company_id INTEGER NOT NULL,
                cnae_code TEXT NOT NULL,
                is_primary INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (company_id, cnae_code),
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY (cnae_code) REFERENCES cnaes(code)
            );

            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS list_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'selected',
                notes TEXT,
                created_at TEXT NOT NULL,
                UNIQUE (list_id, company_id),
                FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT,
                UNIQUE (org_id, name),
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS company_tags (
                company_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (company_id, tag_id),
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS saved_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                filters_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS import_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                source_path TEXT,
                source_url TEXT,
                status TEXT NOT NULL,
                total_rows INTEGER DEFAULT 0,
                imported_rows INTEGER DEFAULT 0,
                error_rows INTEGER DEFAULT 0,
                message TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT
            );

            CREATE TABLE IF NOT EXISTS source_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot TEXT NOT NULL,
                filename TEXT NOT NULL,
                url TEXT NOT NULL,
                size_bytes INTEGER DEFAULT 0,
                etag TEXT,
                local_path TEXT,
                status TEXT NOT NULL DEFAULT 'discovered',
                downloaded_at TEXT,
                imported_at TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE (snapshot, filename)
            );

            CREATE TABLE IF NOT EXISTS email_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                company_id INTEGER,
                list_id INTEGER,
                classification TEXT NOT NULL,
                score INTEGER NOT NULL,
                reasons TEXT,
                validated_at TEXT NOT NULL,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
                FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS known_shared_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                domain TEXT NOT NULL UNIQUE,
                inferred_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS email_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                email TEXT NOT NULL,
                domain TEXT NOT NULL,
                area TEXT,
                classification TEXT NOT NULL,
                score INTEGER NOT NULL,
                labels_json TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                is_shared_contact INTEGER NOT NULL DEFAULT 0,
                is_shared_domain INTEGER NOT NULL DEFAULT 0,
                shared_company_count INTEGER NOT NULL DEFAULT 0,
                shared_domain_count INTEGER NOT NULL DEFAULT 0,
                algorithm_version TEXT NOT NULL,
                classified_at TEXT NOT NULL,
                UNIQUE (company_id, email),
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS email_score_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                email TEXT NOT NULL,
                previous_score INTEGER,
                new_score INTEGER NOT NULL,
                reasons_json TEXT NOT NULL,
                algorithm_version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS suppression_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                email TEXT NOT NULL UNIQUE,
                reason TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS opt_outs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                email TEXT NOT NULL UNIQUE,
                requested_by TEXT,
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS data_subject_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                requester_name TEXT,
                requester_email TEXT NOT NULL,
                request_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                notes TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS export_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                user_id INTEGER,
                list_id INTEGER NOT NULL,
                file_format TEXT NOT NULL,
                declared_purpose TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                columns_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_companies_cnpj ON companies(cnpj);
            CREATE INDEX IF NOT EXISTS idx_companies_root ON companies(cnpj_root);
            CREATE INDEX IF NOT EXISTS idx_companies_legal_name ON companies(legal_name);
            CREATE INDEX IF NOT EXISTS idx_companies_trade_name ON companies(trade_name);
            CREATE INDEX IF NOT EXISTS idx_companies_cnae ON companies(main_cnae_code);
            CREATE INDEX IF NOT EXISTS idx_companies_city ON companies(city);
            CREATE INDEX IF NOT EXISTS idx_companies_state ON companies(state);
            CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);
            CREATE INDEX IF NOT EXISTS idx_companies_size ON companies(size);
            CREATE INDEX IF NOT EXISTS idx_companies_capital ON companies(capital_social);
            CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(email);
            CREATE INDEX IF NOT EXISTS idx_partners_name ON partners(name);
            CREATE INDEX IF NOT EXISTS idx_email_classifications_score ON email_classifications(score);
            CREATE INDEX IF NOT EXISTS idx_email_classifications_domain ON email_classifications(domain);
            CREATE INDEX IF NOT EXISTS idx_known_shared_domains_domain ON known_shared_domains(domain);
            CREATE INDEX IF NOT EXISTS idx_list_companies_list ON list_companies(list_id);
            CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
            CREATE INDEX IF NOT EXISTS idx_source_files_snapshot ON source_files(snapshot);
            """
        )
        seed_core(conn)


def seed_core(conn):
    exists = conn.execute("SELECT id FROM organizations LIMIT 1").fetchone()
    if exists:
        return

    created_at = now_iso()
    cursor = conn.execute(
        "INSERT INTO organizations (name, created_at) VALUES (?, ?)",
        ("Workspace interno", created_at),
    )
    org_id = cursor.lastrowid
    conn.execute(
        """
        INSERT INTO users (org_id, name, email, role, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (org_id, "Operador interno", "admin@localhost", "admin", created_at),
    )
