param(
    [Parameter(Mandatory = $true)]
    [string]$Snapshot,

    [string]$SourceDir = "",
    [string]$Families = "",
    [int]$Limit = 0,
    [string]$Service = "postgres",
    [string]$ExtractRoot = "data/postgres/imports",
    [string]$ContainerDir = "/tmp/radar-cnpj-staging"
)

$ErrorActionPreference = "Stop"

function Format-Bytes {
    param([double]$Bytes)
    if ($Bytes -ge 1GB) {
        return "{0:N2} GB" -f ($Bytes / 1GB)
    }
    if ($Bytes -ge 1MB) {
        return "{0:N2} MB" -f ($Bytes / 1MB)
    }
    if ($Bytes -ge 1KB) {
        return "{0:N2} KB" -f ($Bytes / 1KB)
    }
    return "{0:N0} B" -f $Bytes
}

function Format-Percent {
    param([double]$Part, [double]$Total)
    if ($Total -le 0) {
        return "0.00%"
    }
    return "{0:N2}%" -f (($Part / $Total) * 100)
}

if (!$SourceDir) {
    $SourceDir = "data/downloads/receita/$Snapshot"
}

if (!(Test-Path $SourceDir)) {
    throw "Diretório do snapshot não encontrado: $SourceDir"
}

if (!$Families -and $Limit -eq 0) {
    & "$PSScriptRoot/check_receita_staging_preflight.ps1" `
        -Snapshot $Snapshot `
        -SourceDir $SourceDir `
        -Service $Service
    if ($LASTEXITCODE -ne 0) {
        throw "Preflight de carga completa falhou com exit code $LASTEXITCODE."
    }
}

$plannerArgs = @(
    "scripts/plan_postgres_staging_snapshot.py",
    "--snapshot", $Snapshot,
    "--source-dir", $SourceDir,
    "--limit", $Limit,
    "--extract-root", $ExtractRoot,
    "--container-dir", $ContainerDir
)
if ($Families) {
    $plannerArgs += @("--families", $Families)
}

$planJson = python @plannerArgs

$plan = $planJson | ConvertFrom-Json

if (!$plan.items -or $plan.items.Count -eq 0) {
    throw "Nenhum ZIP oficial reconhecido em $SourceDir"
}

$totalFiles = $plan.items.Count
$totalBytes = 0
foreach ($item in $plan.items) {
    $totalBytes += [int64]($item.zip_size_bytes)
}

Write-Output "Importando snapshot $Snapshot com $totalFiles arquivo(s), $(Format-Bytes $totalBytes) planejados."

$imported = 0
$importedBytes = 0
foreach ($item in $plan.items) {
    $currentFile = $imported + 1
    $itemBytes = [int64]($item.zip_size_bytes)
    $filePercentBefore = Format-Percent $imported $totalFiles
    $bytePercentBefore = Format-Percent $importedBytes $totalBytes
    Write-Output (
        "[{0}/{1} | {2} arquivos | {3} bytes] Iniciando {4} ({5}) -> {6}" -f
        $currentFile,
        $totalFiles,
        $filePercentBefore,
        $bytePercentBefore,
        $item.filename,
        (Format-Bytes $itemBytes),
        $item.table
    )
    & "$PSScriptRoot/import_postgres_staging_file.ps1" `
        -Snapshot $Snapshot `
        -Filename $item.filename `
        -ZipPath $item.zip_path `
        -Service $Service `
        -ExtractRoot $ExtractRoot `
        -ContainerDir $ContainerDir
    $imported += 1
    $importedBytes += $itemBytes
    Write-Output (
        "[{0}/{1} | {2} arquivos | {3} bytes] Concluido {4}" -f
        $imported,
        $totalFiles,
        (Format-Percent $imported $totalFiles),
        (Format-Percent $importedBytes $totalBytes),
        $item.filename
    )
}

Write-Output "Snapshot importado para staging: $Snapshot ($imported arquivo(s), $(Format-Bytes $importedBytes))."
