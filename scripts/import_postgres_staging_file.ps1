param(
    [Parameter(Mandatory = $true)]
    [string]$Snapshot,

    [Parameter(Mandatory = $true)]
    [string]$Filename,

    [string]$ZipPath = "",
    [string]$CsvPath = "",
    [string]$Service = "postgres",
    [string]$ExtractRoot = "data/postgres/imports",
    [string]$ContainerDir = "/tmp/radar-cnpj-staging"
)

$ErrorActionPreference = "Stop"

if (!$ZipPath -and !$CsvPath) {
    throw "Informe ZipPath ou CsvPath."
}

$containerId = docker compose ps -q $Service
if (-not $containerId) {
    throw "Serviço '$Service' não está rodando. Use: docker compose up -d postgres"
}

& "$PSScriptRoot/apply_postgres_migrations.ps1" -Service $Service

$manifestJson = python scripts/plan_postgres_staging_import.py `
    --snapshot $Snapshot `
    --filename $Filename `
    --zip-path $ZipPath `
    --csv-path $CsvPath `
    --extract-root $ExtractRoot `
    --container-dir $ContainerDir

$manifest = $manifestJson | ConvertFrom-Json

if ($ZipPath) {
    if (!(Test-Path $ZipPath)) {
        throw "ZIP não encontrado: $ZipPath"
    }
    if (!(Test-Path $manifest.extract_dir)) {
        New-Item -ItemType Directory -Path $manifest.extract_dir | Out-Null
    }
    python -m zipfile -e $ZipPath $manifest.extract_dir
}

if (!(Test-Path $manifest.local_csv_path)) {
    throw "CSV extraído não encontrado: $($manifest.local_csv_path)"
}

$containerCsvDir = Split-Path -Parent $manifest.container_csv_path
docker compose exec -T $Service sh -c "mkdir -p '$containerCsvDir'"
docker compose cp $manifest.local_csv_path "${Service}:$($manifest.container_csv_path)"

$postgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "radar_cnpj" }
$postgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "radar_cnpj" }

$manifest.import_sql | docker compose exec -T $Service psql `
    -v ON_ERROR_STOP=1 `
    -U $postgresUser `
    -d $postgresDb `
    -X `
    -f -

docker compose exec -T $Service sh -c "rm -f '$($manifest.container_csv_path)'"

Write-Output "Importação concluída: $($manifest.filename) -> $($manifest.table)"
