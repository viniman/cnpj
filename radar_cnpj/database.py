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

            CREATE TABLE IF NOT EXISTS company_enrichment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL UNIQUE,
                source_url TEXT,
                source_type TEXT NOT NULL,
                detected_domain TEXT,
                emails_json TEXT NOT NULL,
                phones_json TEXT NOT NULL,
                social_links_json TEXT NOT NULL,
                technologies_json TEXT NOT NULL,
                digital_maturity_score INTEGER NOT NULL DEFAULT 0,
                reasons_json TEXT NOT NULL,
                confidence TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS scraping_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                url TEXT,
                status TEXT NOT NULL,
                message TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS scraping_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                status_code INTEGER NOT NULL DEFAULT 0,
                headers_json TEXT NOT NULL,
                body_hash TEXT NOT NULL,
                body_text TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                company_id INTEGER,
                list_id INTEGER,
                email TEXT NOT NULL DEFAULT '',
                segment TEXT,
                source TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'new',
                block_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (org_id, company_id, list_id, email),
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
                FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                niche TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                cta_url TEXT,
                daily_limit INTEGER NOT NULL DEFAULT 50,
                interval_seconds INTEGER NOT NULL DEFAULT 300,
                bounce_pause_threshold REAL NOT NULL DEFAULT 0.02,
                complaint_pause_threshold REAL NOT NULL DEFAULT 0.0005,
                mode TEXT NOT NULL DEFAULT 'simulated',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS campaign_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                cta_url TEXT,
                utm_content TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                campaign_id INTEGER NOT NULL,
                variant_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                status TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'simulated',
                provider_message_id TEXT,
                block_reason TEXT,
                scheduled_at TEXT,
                sent_at TEXT,
                utm_url TEXT,
                created_at TEXT NOT NULL,
                UNIQUE (lead_id, campaign_id, variant_id),
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                FOREIGN KEY (variant_id) REFERENCES campaign_variants(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                send_id INTEGER,
                lead_id INTEGER,
                campaign_id INTEGER,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'simulated',
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (send_id) REFERENCES sends(id) ON DELETE SET NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                campaign_id INTEGER,
                conversion_type TEXT NOT NULL,
                utm_json TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS throttle_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL UNIQUE,
                daily_limit INTEGER NOT NULL DEFAULT 50,
                interval_seconds INTEGER NOT NULL DEFAULT 300,
                bounce_pause_threshold REAL NOT NULL DEFAULT 0.02,
                complaint_pause_threshold REAL NOT NULL DEFAULT 0.0005,
                warmup_day INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS pause_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                pause_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                purpose TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS email_template_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                variables_json TEXT NOT NULL,
                compliance_footer TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE (template_id, version_number),
                FOREIGN KEY (template_id) REFERENCES email_templates(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                campaign_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS sequence_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                name TEXT NOT NULL,
                step_type TEXT NOT NULL DEFAULT 'email',
                wait_days INTEGER NOT NULL DEFAULT 0,
                template_id INTEGER NOT NULL,
                template_version_id INTEGER NOT NULL,
                require_approval INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE (sequence_id, step_number),
                FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE,
                FOREIGN KEY (template_id) REFERENCES email_templates(id),
                FOREIGN KEY (template_version_id) REFERENCES email_template_versions(id)
            );

            CREATE TABLE IF NOT EXISTS lead_journey (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                lead_id INTEGER NOT NULL,
                sequence_id INTEGER NOT NULL,
                current_step_id INTEGER,
                current_step_number INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL,
                next_action_at TEXT,
                last_action_at TEXT,
                block_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (org_id, lead_id, sequence_id),
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
                FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE,
                FOREIGN KEY (current_step_id) REFERENCES sequence_steps(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS approval_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                title TEXT NOT NULL,
                context_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                decision_note TEXT,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                lead_id INTEGER,
                sequence_id INTEGER,
                action_type TEXT NOT NULL,
                source TEXT NOT NULL,
                reason TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS icp_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                criteria_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS lead_priority_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                icp_rule_id INTEGER NOT NULL,
                lead_id INTEGER,
                company_id INTEGER NOT NULL,
                list_id INTEGER,
                status TEXT NOT NULL DEFAULT 'suggested',
                priority_score INTEGER NOT NULL DEFAULT 0,
                fit_score INTEGER NOT NULL DEFAULT 0,
                reason_json TEXT NOT NULL,
                decision_note TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (org_id, icp_rule_id, company_id, list_id),
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (icp_rule_id) REFERENCES icp_rules(id) ON DELETE CASCADE,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS reply_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                lead_id INTEGER,
                send_id INTEGER,
                email TEXT NOT NULL,
                subject TEXT,
                body_text TEXT NOT NULL,
                classification TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0,
                reasons_json TEXT NOT NULL,
                raw_payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (send_id) REFERENCES sends(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS handoffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                lead_id INTEGER,
                reply_classification_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                priority TEXT NOT NULL DEFAULT 'medium',
                reason TEXT NOT NULL,
                context_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                resolution_note TEXT,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                FOREIGN KEY (reply_classification_id) REFERENCES reply_classifications(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                lead_id INTEGER NOT NULL,
                company_id INTEGER,
                reply_classification_id INTEGER,
                handoff_id INTEGER,
                status TEXT NOT NULL DEFAULT 'scheduled',
                title TEXT NOT NULL,
                attendee_email TEXT NOT NULL,
                scheduled_at TEXT,
                duration_minutes INTEGER NOT NULL DEFAULT 30,
                meeting_url TEXT,
                owner_name TEXT,
                notes TEXT,
                outcome_note TEXT,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
                FOREIGN KEY (reply_classification_id) REFERENCES reply_classifications(id) ON DELETE SET NULL,
                FOREIGN KEY (handoff_id) REFERENCES handoffs(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS kpi_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                kpi_key TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                formula TEXT NOT NULL,
                unit TEXT NOT NULL DEFAULT 'count',
                direction TEXT NOT NULL DEFAULT 'increase',
                source_tables_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (org_id, kpi_key),
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS objectives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                period_start TEXT,
                period_end TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id)
            );

            CREATE TABLE IF NOT EXISTS key_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                objective_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                kpi_key TEXT NOT NULL,
                target_value REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (objective_id) REFERENCES objectives(id) ON DELETE CASCADE
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
            CREATE INDEX IF NOT EXISTS idx_company_enrichment_domain ON company_enrichment(detected_domain);
            CREATE INDEX IF NOT EXISTS idx_company_enrichment_score ON company_enrichment(digital_maturity_score);
            CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
            CREATE INDEX IF NOT EXISTS idx_scraping_cache_expires ON scraping_cache(expires_at);
            CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
            CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
            CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
            CREATE INDEX IF NOT EXISTS idx_sends_campaign ON sends(campaign_id);
            CREATE INDEX IF NOT EXISTS idx_sends_status ON sends(status);
            CREATE INDEX IF NOT EXISTS idx_events_campaign_type ON events(campaign_id, event_type);
            CREATE INDEX IF NOT EXISTS idx_email_templates_status ON email_templates(status);
            CREATE INDEX IF NOT EXISTS idx_email_template_versions_active ON email_template_versions(template_id, is_active);
            CREATE INDEX IF NOT EXISTS idx_sequences_status ON sequences(status);
            CREATE INDEX IF NOT EXISTS idx_sequence_steps_sequence ON sequence_steps(sequence_id, step_number);
            CREATE INDEX IF NOT EXISTS idx_lead_journey_status ON lead_journey(status);
            CREATE INDEX IF NOT EXISTS idx_approval_queue_status ON approval_queue(status);
            CREATE INDEX IF NOT EXISTS idx_agent_actions_created ON agent_actions(created_at);
            CREATE INDEX IF NOT EXISTS idx_icp_rules_status ON icp_rules(status);
            CREATE INDEX IF NOT EXISTS idx_lead_priority_rule ON lead_priority_queue(icp_rule_id, status);
            CREATE INDEX IF NOT EXISTS idx_lead_priority_score ON lead_priority_queue(priority_score);
            CREATE INDEX IF NOT EXISTS idx_reply_classifications_created ON reply_classifications(created_at);
            CREATE INDEX IF NOT EXISTS idx_reply_classifications_class ON reply_classifications(classification);
            CREATE INDEX IF NOT EXISTS idx_handoffs_status ON handoffs(status);
            CREATE INDEX IF NOT EXISTS idx_handoffs_priority ON handoffs(priority);
            CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
            CREATE INDEX IF NOT EXISTS idx_meetings_lead ON meetings(lead_id);
            CREATE INDEX IF NOT EXISTS idx_meetings_scheduled ON meetings(scheduled_at);
            CREATE INDEX IF NOT EXISTS idx_kpi_definitions_key ON kpi_definitions(org_id, kpi_key);
            CREATE INDEX IF NOT EXISTS idx_objectives_status ON objectives(org_id, status);
            CREATE INDEX IF NOT EXISTS idx_key_results_objective ON key_results(objective_id);
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
