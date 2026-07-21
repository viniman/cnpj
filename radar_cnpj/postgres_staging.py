import os
import re
import zipfile


SCHEMA_NAME = "receita_staging"
COPY_OPTIONS = "WITH (FORMAT csv, DELIMITER ';', QUOTE '\"', ESCAPE '\"', ENCODING 'LATIN1')"

CHUNKED_FILE_PREFIXES = {
    "empresas": "empresas",
    "estabelecimentos": "estabelecimentos",
    "socios": "socios",
}

DOMAIN_FILE_FAMILIES = {
    "cnaes.zip": "cnaes",
    "motivos.zip": "motivos",
    "municipios.zip": "municipios",
    "naturezas.zip": "naturezas",
    "paises.zip": "paises",
    "qualificacoes.zip": "qualificacoes",
    "simples.zip": "simples",
}

TABLE_DEFINITIONS = {
    "empresas": {
        "table": "empresas_raw",
        "columns": [
            "cnpj_basico",
            "razao_social",
            "natureza_juridica",
            "qualificacao_responsavel",
            "capital_social",
            "porte_empresa",
            "ente_federativo_responsavel",
        ],
    },
    "estabelecimentos": {
        "table": "estabelecimentos_raw",
        "columns": [
            "cnpj_basico",
            "cnpj_ordem",
            "cnpj_dv",
            "identificador_matriz_filial",
            "nome_fantasia",
            "situacao_cadastral",
            "data_situacao_cadastral",
            "motivo_situacao_cadastral",
            "nome_cidade_exterior",
            "pais",
            "data_inicio_atividade",
            "cnae_fiscal_principal",
            "cnae_fiscal_secundaria",
            "tipo_logradouro",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cep",
            "uf",
            "municipio",
            "ddd_1",
            "telefone_1",
            "ddd_2",
            "telefone_2",
            "ddd_fax",
            "fax",
            "correio_eletronico",
            "situacao_especial",
            "data_situacao_especial",
        ],
    },
    "socios": {
        "table": "socios_raw",
        "columns": [
            "cnpj_basico",
            "identificador_socio",
            "nome_socio_razao_social",
            "cnpj_cpf_socio",
            "qualificacao_socio",
            "data_entrada_sociedade",
            "pais",
            "representante_legal",
            "nome_representante",
            "qualificacao_representante",
            "faixa_etaria",
        ],
    },
    "cnaes": {"table": "cnaes_raw", "columns": ["codigo", "descricao"]},
    "motivos": {"table": "motivos_raw", "columns": ["codigo", "descricao"]},
    "municipios": {"table": "municipios_raw", "columns": ["codigo", "descricao"]},
    "naturezas": {"table": "naturezas_raw", "columns": ["codigo", "descricao"]},
    "paises": {"table": "paises_raw", "columns": ["codigo", "descricao"]},
    "qualificacoes": {"table": "qualificacoes_raw", "columns": ["codigo", "descricao"]},
    "simples": {
        "table": "simples_raw",
        "columns": [
            "cnpj_basico",
            "opcao_simples",
            "data_opcao_simples",
            "data_exclusao_simples",
            "opcao_mei",
            "data_opcao_mei",
            "data_exclusao_mei",
        ],
    },
}


def validate_identifier(value):
    value = str(value or "").strip()
    if not re.match(r"^[a-z_][a-z0-9_]*$", value):
        raise ValueError("Identificador Postgres invalido: %s" % value)
    return value


def sql_literal(value):
    return "'" + str(value or "").replace("'", "''") + "'"


def psql_path(value):
    return str(value or "").replace("\\", "/").replace("'", "''")


def shell_quote(value):
    return '"' + str(value or "").replace('"', '\\"') + '"'


def official_file_family(filename):
    base = os.path.basename(str(filename or "")).strip()
    lower = base.lower()
    if lower in DOMAIN_FILE_FAMILIES:
        family = DOMAIN_FILE_FAMILIES[lower]
        return {
            "filename": base,
            "family": family,
            "chunk": None,
            "table": TABLE_DEFINITIONS[family]["table"],
            "columns": TABLE_DEFINITIONS[family]["columns"],
        }

    match = re.match(r"^(empresas|estabelecimentos|socios)(\d+)\.zip$", lower)
    if not match:
        return None
    family = CHUNKED_FILE_PREFIXES[match.group(1)]
    return {
        "filename": base,
        "family": family,
        "chunk": int(match.group(2)),
        "table": TABLE_DEFINITIONS[family]["table"],
        "columns": TABLE_DEFINITIONS[family]["columns"],
    }


def expected_official_filenames(chunks=range(10)):
    filenames = []
    for chunk in chunks:
        filenames.extend(
            [
                "Empresas%s.zip" % chunk,
                "Estabelecimentos%s.zip" % chunk,
                "Socios%s.zip" % chunk,
            ]
        )
    filenames.extend(
        [
            "Cnaes.zip",
            "Motivos.zip",
            "Municipios.zip",
            "Naturezas.zip",
            "Paises.zip",
            "Qualificacoes.zip",
            "Simples.zip",
        ]
    )
    return filenames


def table_sql(schema_name, definition):
    schema = validate_identifier(schema_name)
    table = validate_identifier(definition["table"])
    columns = ["    %s text" % validate_identifier(column) for column in definition["columns"]]
    columns.extend(
        [
            "    snapshot text",
            "    chunk integer",
            "    source_file text",
            "    loaded_at timestamptz NOT NULL DEFAULT now()",
        ]
    )
    return "CREATE TABLE IF NOT EXISTS %s.%s (\n%s\n);" % (schema, table, ",\n".join(columns))


def postgres_staging_schema(schema_name=SCHEMA_NAME):
    schema = validate_identifier(schema_name)
    blocks = [
        "CREATE EXTENSION IF NOT EXISTS unaccent;",
        "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
        "CREATE SCHEMA IF NOT EXISTS %s;" % schema,
    ]
    for definition in TABLE_DEFINITIONS.values():
        blocks.append(table_sql(schema, definition))
    blocks.extend(
        [
            "CREATE INDEX IF NOT EXISTS idx_receita_empresas_cnpj_basico ON %s.empresas_raw (cnpj_basico);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_empresas_razao_trgm ON %s.empresas_raw USING gin (razao_social gin_trgm_ops);" % schema,
            (
                "CREATE INDEX IF NOT EXISTS idx_receita_estab_cnpj_completo "
                "ON %s.estabelecimentos_raw ((cnpj_basico || cnpj_ordem || cnpj_dv));" % schema
            ),
            "CREATE INDEX IF NOT EXISTS idx_receita_estab_cnae ON %s.estabelecimentos_raw (cnae_fiscal_principal);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_estab_uf_municipio ON %s.estabelecimentos_raw (uf, municipio);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_estab_email ON %s.estabelecimentos_raw (correio_eletronico);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_estab_fantasia_trgm ON %s.estabelecimentos_raw USING gin (nome_fantasia gin_trgm_ops);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_socios_cnpj_basico ON %s.socios_raw (cnpj_basico);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_socios_nome_trgm ON %s.socios_raw USING gin (nome_socio_razao_social gin_trgm_ops);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_cnaes_codigo ON %s.cnaes_raw (codigo);" % schema,
            "CREATE INDEX IF NOT EXISTS idx_receita_municipios_codigo ON %s.municipios_raw (codigo);" % schema,
        ]
    )
    return "\n\n".join(blocks) + "\n"


def source_row_to_dict(row):
    return dict(row) if not isinstance(row, dict) else dict(row)


def safe_zip_member(member):
    member = os.path.normpath(str(member or "")).lstrip("\\/")
    if member.startswith(".."):
        return os.path.basename(member)
    return member


def csv_member_for_zip(zip_path, fallback_name):
    if not zip_path or not os.path.exists(zip_path):
        return fallback_name
    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
    except (OSError, zipfile.BadZipFile):
        return fallback_name
    csv_members = [name for name in members if name.lower().endswith(".csv")]
    return safe_zip_member((csv_members or members or [fallback_name])[0])


def copy_command(schema_name, table, columns, csv_path):
    schema = validate_identifier(schema_name)
    table = validate_identifier(table)
    column_list = ", ".join(validate_identifier(column) for column in columns)
    return "\\copy %s.%s (%s) FROM '%s' %s;" % (
        schema,
        table,
        column_list,
        psql_path(csv_path),
        COPY_OPTIONS,
    )


def metadata_update_sql(schema_name, table, snapshot, chunk, filename):
    schema = validate_identifier(schema_name)
    table = validate_identifier(table)
    chunk_value = "NULL" if chunk is None else str(int(chunk))
    return (
        "UPDATE %s.%s SET snapshot = %s, chunk = %s, source_file = %s "
        "WHERE source_file IS NULL;"
        % (schema, table, sql_literal(snapshot), chunk_value, sql_literal(filename))
    )


def build_copy_plan_item(snapshot, file_row, schema_name=SCHEMA_NAME, extract_root=None):
    row = source_row_to_dict(file_row)
    classification = official_file_family(row.get("filename"))
    if not classification:
        return None

    local_path = row.get("local_path") or row.get("path") or ""
    is_available = bool(local_path and os.path.exists(local_path))
    filename = classification["filename"]
    stem = os.path.splitext(filename)[0]
    root = extract_root or os.path.join(os.path.dirname(local_path), "extracted") if local_path else ""
    extract_dir = os.path.abspath(os.path.join(root, stem)) if root else ""
    csv_member = csv_member_for_zip(local_path, stem + ".CSV")
    csv_path = os.path.abspath(os.path.join(extract_dir, csv_member)) if extract_dir else ""

    item = {
        "filename": filename,
        "family": classification["family"],
        "chunk": classification["chunk"],
        "table": "%s.%s" % (schema_name, classification["table"]),
        "columns": classification["columns"],
        "size_bytes": int(row.get("size_bytes") or 0),
        "status": row.get("status") or "unknown",
        "source_zip_path": os.path.abspath(local_path) if local_path else "",
        "extract_dir": extract_dir,
        "csv_member": csv_member,
        "csv_path": csv_path,
        "available": is_available,
    }
    if is_available:
        item["extract_command"] = "python -m zipfile -e %s %s" % (shell_quote(local_path), shell_quote(extract_dir))
        item["copy_sql"] = "\n".join(
            [
                "BEGIN;",
                copy_command(schema_name, classification["table"], classification["columns"], csv_path),
                metadata_update_sql(schema_name, classification["table"], snapshot, classification["chunk"], filename),
                "COMMIT;",
            ]
        )
    else:
        item["extract_command"] = ""
        item["copy_sql"] = ""
    return item


def build_postgres_staging_plan(snapshot, source_files, schema_name=SCHEMA_NAME, extract_root=None):
    snapshot = str(snapshot or "").strip()
    rows = [source_row_to_dict(row) for row in (source_files or [])]
    if not snapshot and rows:
        snapshot = str(rows[0].get("snapshot") or "").strip()

    expected = expected_official_filenames()
    present = {str(row.get("filename") or "").lower(): row for row in rows}
    items = []
    unavailable = []
    ignored = []
    for row in rows:
        item = build_copy_plan_item(snapshot, row, schema_name=schema_name, extract_root=extract_root)
        if not item:
            ignored.append(row.get("filename") or "")
            continue
        if item["available"]:
            items.append(item)
        else:
            unavailable.append(item)

    missing = [
        {"filename": filename, "reason": "Arquivo oficial ainda nao registrado em source_files"}
        for filename in expected
        if filename.lower() not in present
    ]
    families = {}
    for item in items + unavailable:
        families[item["family"]] = families.get(item["family"], 0) + 1

    return {
        "snapshot": snapshot,
        "schema_name": schema_name,
        "ddl_sql": postgres_staging_schema(schema_name),
        "copy_plan": items,
        "unavailable_files": unavailable,
        "missing_files": missing,
        "ignored_files": ignored,
        "expected_files": expected,
        "summary": {
            "source_files": len(rows),
            "recognized_files": len(items) + len(unavailable),
            "available_files": len(items),
            "unavailable_files": len(unavailable),
            "missing_files": len(missing),
            "total_available_bytes": sum(item["size_bytes"] for item in items),
            "families": families,
        },
        "guardrails": [
            "Execute este plano em uma instancia PostgreSQL dedicada para carga nacional.",
            "Extraia cada ZIP antes do psql copy e confira o membro CSV detectado.",
            "Use staging como area bruta; transforme para tabelas finais em lote separado.",
            "Confira contagens por tabela antes de substituir dados produtivos.",
            "Mantenha supressao, opt-out e LGPD nos fluxos que usam emails carregados.",
        ],
    }
