param(
    [Parameter(Mandatory = $true)]
    [string]$Snapshot,

    [string]$Families = "",
    [string]$Service = "postgres",
    [switch]$RequireData
)

$ErrorActionPreference = "Stop"

function Sql-Literal {
    param([string]$Value)
    return "'" + (($Value -as [string]) -replace "'", "''") + "'"
}

$tableByFamily = [ordered]@{
    cnaes = "cnaes_raw"
    motivos = "motivos_raw"
    municipios = "municipios_raw"
    naturezas = "naturezas_raw"
    paises = "paises_raw"
    qualificacoes = "qualificacoes_raw"
    simples = "simples_raw"
    empresas = "empresas_raw"
    estabelecimentos = "estabelecimentos_raw"
    socios = "socios_raw"
}

$selectedFamilies = @()
if ($Families) {
    $selectedFamilies = $Families.Split(",") | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ }
} else {
    $selectedFamilies = @($tableByFamily.Keys)
}

foreach ($family in $selectedFamilies) {
    if (!$tableByFamily.Contains($family)) {
        throw "Familia de staging desconhecida: $family"
    }
}

$containerId = docker compose ps -q $Service
if (-not $containerId) {
    throw "Servico '$Service' nao esta rodando. Use: docker compose up -d postgres"
}

$postgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "radar_cnpj" }
$postgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "radar_cnpj" }
$snapshotLiteral = Sql-Literal $Snapshot

$selects = @()
foreach ($family in $selectedFamilies) {
    $table = $tableByFamily[$family]
    $selects += "SELECT '$family' AS family, '$table' AS table_name, count(*)::bigint AS row_count FROM receita_staging.$table WHERE snapshot = $snapshotLiteral"
}

$sql = @"
WITH counts AS (
$(($selects -join "`nUNION ALL`n"))
)
SELECT family || '|' || table_name || '|' || row_count
FROM counts
ORDER BY family;
"@

$lines = $sql | docker compose exec -T $Service psql `
    -v ON_ERROR_STOP=1 `
    -U $postgresUser `
    -d $postgresDb `
    -X `
    -t `
    -A `
    -q `
    -f -

if ($LASTEXITCODE -ne 0) {
    throw "Consulta de contagens do staging falhou com exit code $LASTEXITCODE."
}

Write-Output "Contagens receita_staging para snapshot $Snapshot"
foreach ($line in $lines) {
    if (!$line) {
        continue
    }
    $parts = $line.Split("|")
    $family = $parts[0]
    $table = $parts[1]
    $count = [int64]$parts[2]
    Write-Output ("{0,-18} {1,-28} {2,12}" -f $family, $table, $count)
    if ($RequireData -and $count -le 0) {
        throw "Tabela receita_staging.$table sem dados para snapshot $Snapshot."
    }
}

Write-Output "Validacao de contagens concluida."
