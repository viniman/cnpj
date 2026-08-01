param(
    [string]$Service = "postgres",
    [string]$MigrationsDir = "infra/postgres/migrations"
)

$ErrorActionPreference = "Stop"

function Sql-Literal {
    param([string]$Value)
    return "'" + (($Value -as [string]) -replace "'", "''") + "'"
}

$containerId = docker compose ps -q $Service
if (-not $containerId) {
    throw "Serviço '$Service' não está rodando. Use: docker compose up -d postgres"
}

if (!(Test-Path $MigrationsDir)) {
    throw "Diretório de migrations não encontrado: $MigrationsDir"
}

$postgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "radar_cnpj" }
$postgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "radar_cnpj" }

function Invoke-Psql {
    param([string]$Sql)
    $Sql | docker compose exec -T $Service psql `
        -v ON_ERROR_STOP=1 `
        -U $postgresUser `
        -d $postgresDb `
        -X `
        -q `
        -f -
}

function Query-Psql {
    param([string]$Sql)
    $Sql | docker compose exec -T $Service psql `
        -v ON_ERROR_STOP=1 `
        -U $postgresUser `
        -d $postgresDb `
        -X `
        -t `
        -A `
        -q `
        -f -
}

Invoke-Psql @"
CREATE SCHEMA IF NOT EXISTS receita_staging;
CREATE TABLE IF NOT EXISTS receita_staging.schema_migrations (
    version text PRIMARY KEY,
    filename text NOT NULL,
    checksum_sha256 text NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now()
);
"@

$migrationFiles = Get-ChildItem -Path $MigrationsDir -Filter "*.sql" | Sort-Object Name
if (!$migrationFiles) {
    throw "Nenhuma migration SQL encontrada em $MigrationsDir"
}

foreach ($file in $migrationFiles) {
    if ($file.Name -notmatch "^(\d{14})_[a-z0-9_]+\.sql$") {
        throw "Nome de migration fora do padrão YYYYMMDDHHMMSS_descriptive_slug.sql: $($file.Name)"
    }

    $version = $Matches[1]
    $checksum = (Get-FileHash -Algorithm SHA256 -Path $file.FullName).Hash.ToLowerInvariant()
    $existingChecksumResult = Query-Psql "SELECT checksum_sha256 FROM receita_staging.schema_migrations WHERE version = $(Sql-Literal $version);"
    $existingChecksum = if ($null -eq $existingChecksumResult) { "" } else { ($existingChecksumResult -as [string]).Trim() }

    if ($existingChecksum) {
        if ($existingChecksum -ne $checksum) {
            throw "Migration $($file.Name) já foi aplicada com checksum diferente."
        }
        Write-Output "SKIP $($file.Name)"
        continue
    }

    $migrationSql = Get-Content -Raw -Path $file.FullName
    $wrappedSql = @"
BEGIN;
$migrationSql
INSERT INTO receita_staging.schema_migrations (version, filename, checksum_sha256)
VALUES ($(Sql-Literal $version), $(Sql-Literal $file.Name), $(Sql-Literal $checksum));
COMMIT;
"@

    Invoke-Psql $wrappedSql
    Write-Output "APPLIED $($file.Name)"
}
