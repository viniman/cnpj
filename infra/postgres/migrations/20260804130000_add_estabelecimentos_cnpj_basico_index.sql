-- Migration: add plain btree index on estabelecimentos_raw.cnpj_basico.
-- Naming convention: YYYYMMDDHHMMSS_descriptive_slug.sql.
-- Scope: staging schema only. Product schemas are owned by NestJS/Prisma.
--
-- Context: the original migration indexed the concatenated full CNPJ
-- expression (cnpj_basico || cnpj_ordem || cnpj_dv) and cnae/uf/email/
-- trigram columns, but not cnpj_basico alone. Joining
-- estabelecimentos_raw to empresas_raw on cnpj_basico (the company
-- search use case, issue #66) had no index to use on the
-- estabelecimentos_raw side, forcing a full sequential scan of 72M rows
-- even when the matching set was small. This index lets that join use
-- an index scan instead.

CREATE INDEX IF NOT EXISTS idx_receita_estab_cnpj_basico
    ON receita_staging.estabelecimentos_raw (cnpj_basico);
