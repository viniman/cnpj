CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS receita_staging;

CREATE TABLE IF NOT EXISTS receita_staging.schema_bootstrap_log (
    id bigserial PRIMARY KEY,
    version text NOT NULL,
    description text NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO receita_staging.schema_bootstrap_log (version, description)
SELECT 'phase-41', 'Local PostgreSQL bootstrap for Receita staging'
WHERE NOT EXISTS (
    SELECT 1
    FROM receita_staging.schema_bootstrap_log
    WHERE version = 'phase-41'
);
