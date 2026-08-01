-- Migration: create Receita Federal raw staging tables.
-- Naming convention: YYYYMMDDHHMMSS_descriptive_slug.sql.
-- Scope: staging schema only. Product schemas are owned by NestJS/Prisma.

CREATE TABLE IF NOT EXISTS receita_staging.empresas_raw (
    cnpj_basico text,
    razao_social text,
    natureza_juridica text,
    qualificacao_responsavel text,
    capital_social text,
    porte_empresa text,
    ente_federativo_responsavel text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.estabelecimentos_raw (
    cnpj_basico text,
    cnpj_ordem text,
    cnpj_dv text,
    identificador_matriz_filial text,
    nome_fantasia text,
    situacao_cadastral text,
    data_situacao_cadastral text,
    motivo_situacao_cadastral text,
    nome_cidade_exterior text,
    pais text,
    data_inicio_atividade text,
    cnae_fiscal_principal text,
    cnae_fiscal_secundaria text,
    tipo_logradouro text,
    logradouro text,
    numero text,
    complemento text,
    bairro text,
    cep text,
    uf text,
    municipio text,
    ddd_1 text,
    telefone_1 text,
    ddd_2 text,
    telefone_2 text,
    ddd_fax text,
    fax text,
    correio_eletronico text,
    situacao_especial text,
    data_situacao_especial text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.socios_raw (
    cnpj_basico text,
    identificador_socio text,
    nome_socio_razao_social text,
    cnpj_cpf_socio text,
    qualificacao_socio text,
    data_entrada_sociedade text,
    pais text,
    representante_legal text,
    nome_representante text,
    qualificacao_representante text,
    faixa_etaria text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.cnaes_raw (
    codigo text,
    descricao text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.motivos_raw (
    codigo text,
    descricao text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.municipios_raw (
    codigo text,
    descricao text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.naturezas_raw (
    codigo text,
    descricao text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.paises_raw (
    codigo text,
    descricao text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.qualificacoes_raw (
    codigo text,
    descricao text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receita_staging.simples_raw (
    cnpj_basico text,
    opcao_simples text,
    data_opcao_simples text,
    data_exclusao_simples text,
    opcao_mei text,
    data_opcao_mei text,
    data_exclusao_mei text,
    snapshot text,
    chunk integer,
    source_file text,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_receita_empresas_cnpj_basico ON receita_staging.empresas_raw (cnpj_basico);
CREATE INDEX IF NOT EXISTS idx_receita_empresas_razao_trgm ON receita_staging.empresas_raw USING gin (razao_social gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_receita_estab_cnpj_completo ON receita_staging.estabelecimentos_raw ((cnpj_basico || cnpj_ordem || cnpj_dv));
CREATE INDEX IF NOT EXISTS idx_receita_estab_cnae ON receita_staging.estabelecimentos_raw (cnae_fiscal_principal);
CREATE INDEX IF NOT EXISTS idx_receita_estab_uf_municipio ON receita_staging.estabelecimentos_raw (uf, municipio);
CREATE INDEX IF NOT EXISTS idx_receita_estab_email ON receita_staging.estabelecimentos_raw (correio_eletronico);
CREATE INDEX IF NOT EXISTS idx_receita_estab_fantasia_trgm ON receita_staging.estabelecimentos_raw USING gin (nome_fantasia gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_receita_socios_cnpj_basico ON receita_staging.socios_raw (cnpj_basico);
CREATE INDEX IF NOT EXISTS idx_receita_socios_nome_trgm ON receita_staging.socios_raw USING gin (nome_socio_razao_social gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_receita_cnaes_codigo ON receita_staging.cnaes_raw (codigo);
CREATE INDEX IF NOT EXISTS idx_receita_municipios_codigo ON receita_staging.municipios_raw (codigo);
