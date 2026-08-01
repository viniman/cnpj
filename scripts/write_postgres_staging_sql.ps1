param(
    [string]$Output = "data/postgres/receita_staging.sql"
)

$ErrorActionPreference = "Stop"

$directory = Split-Path -Parent $Output
if ($directory -and !(Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory | Out-Null
}

python -c "from radar_cnpj.postgres_staging import postgres_staging_schema; print(postgres_staging_schema())" | Out-File -FilePath $Output -Encoding utf8
Write-Output "DDL PostgreSQL staging escrita em $Output"
