param(
    [Parameter(Mandatory = $true)]
    [string]$Snapshot,

    [string]$SourceDir = "",
    [double]$DiskMultiplier = 3.0,
    [string]$Service = "postgres"
)

$ErrorActionPreference = "Stop"

if (!$SourceDir) {
    $SourceDir = "data/downloads/receita/$Snapshot"
}

$freeBytes = -1
if (Test-Path $SourceDir) {
    $sourceItem = Get-Item -LiteralPath $SourceDir
    if ($sourceItem.PSDrive -and $null -ne $sourceItem.PSDrive.Free) {
        $freeBytes = [int64]$sourceItem.PSDrive.Free
    }
}

$statusJson = python scripts/plan_receita_base_status.py `
    --snapshot $Snapshot `
    --source-dir $SourceDir `
    --free-bytes $freeBytes `
    --disk-multiplier $DiskMultiplier

$report = $statusJson | ConvertFrom-Json
$statusJson

Write-Output "Status consolidado: $($report.status)"
Write-Output "Proximo gate: $($report.next_gate.key) - $($report.next_gate.message)"

$containerId = docker compose ps --status running -q $Service
if ($containerId) {
    Write-Output "Postgres Docker: container em execucao ($Service)."
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
        -Snapshot $Snapshot `
        -Families cnaes,municipios,naturezas `
        -RequireData
} else {
    Write-Output "Postgres Docker: container em execucao nao encontrado. Use docker compose up -d postgres para validar contagens."
}
