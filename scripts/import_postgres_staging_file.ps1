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

function Container-ParentPath {
    param([string]$Path)
    $normalized = ($Path -as [string]).Replace("\", "/")
    $lastSlash = $normalized.LastIndexOf("/")
    if ($lastSlash -le 0) {
        return "."
    }
    return $normalized.Substring(0, $lastSlash)
}

$containerId = docker compose ps -q $Service
if (-not $containerId) {
    throw "Serviço '$Service' não está rodando. Use: docker compose up -d postgres"
}

& "$PSScriptRoot/apply_postgres_migrations.ps1" -Service $Service
if ($LASTEXITCODE -ne 0) {
    throw "Aplicacao de migrations falhou com exit code $LASTEXITCODE."
}

$plannerArgs = @(
    "scripts/plan_postgres_staging_import.py",
    "--snapshot", $Snapshot,
    "--filename", $Filename,
    "--extract-root", $ExtractRoot,
    "--container-dir", $ContainerDir
)
if ($ZipPath) {
    $plannerArgs += @("--zip-path", $ZipPath)
}
if ($CsvPath) {
    $plannerArgs += @("--csv-path", $CsvPath)
}

$manifestJson = python @plannerArgs
if ($LASTEXITCODE -ne 0) {
    throw "Planejamento da importacao falhou com exit code $LASTEXITCODE."
}

$manifest = $manifestJson | ConvertFrom-Json
if (!$manifest) {
    throw "Planner nao retornou manifesto de importacao."
}

if ($ZipPath) {
    if (!(Test-Path $ZipPath)) {
        throw "ZIP não encontrado: $ZipPath"
    }
    if (!(Test-Path $manifest.extract_dir)) {
        New-Item -ItemType Directory -Path $manifest.extract_dir | Out-Null
    }
    python -m zipfile -e $ZipPath $manifest.extract_dir
    if ($LASTEXITCODE -ne 0) {
        throw "Extracao do ZIP falhou com exit code $LASTEXITCODE."
    }
}

if (!(Test-Path $manifest.local_csv_path)) {
    throw "CSV extraído não encontrado: $($manifest.local_csv_path)"
}

$containerCsvDir = Container-ParentPath $manifest.container_csv_path
docker compose exec -T $Service sh -c "mkdir -p '$containerCsvDir'"
if ($LASTEXITCODE -ne 0) {
    throw "Criacao de diretorio no container falhou com exit code $LASTEXITCODE."
}
docker compose cp $manifest.local_csv_path "${Service}:$containerCsvDir/"
if ($LASTEXITCODE -ne 0) {
    throw "Copia do CSV para o container falhou com exit code $LASTEXITCODE."
}

$postgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "radar_cnpj" }
$postgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "radar_cnpj" }

$manifest.import_sql | docker compose exec -T $Service psql `
    -v ON_ERROR_STOP=1 `
    -U $postgresUser `
    -d $postgresDb `
    -X `
    -f -
if ($LASTEXITCODE -ne 0) {
    throw "COPY no Postgres falhou com exit code $LASTEXITCODE."
}

docker compose exec -T $Service sh -c "rm -f '$($manifest.container_csv_path)'"

if ($ZipPath -and $manifest.extract_dir -and (Test-Path $manifest.extract_dir)) {
    Remove-Item -LiteralPath $manifest.extract_dir -Recurse -Force
}

Write-Output "Importação concluída: $($manifest.filename) -> $($manifest.table)"
