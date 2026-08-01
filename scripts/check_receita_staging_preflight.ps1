param(
    [Parameter(Mandatory = $true)]
    [string]$Snapshot,

    [string]$SourceDir = "",
    [string]$Families = "",
    [int]$Limit = 0,
    [int]$ExpectedFiles = 37,
    [string]$Service = "postgres",
    [switch]$SkipDockerCheck
)

$ErrorActionPreference = "Stop"

if (!$SourceDir) {
    $SourceDir = "data/downloads/receita/$Snapshot"
}

$preflightArgs = @(
    "scripts/plan_receita_staging_preflight.py",
    "--snapshot", $Snapshot,
    "--source-dir", $SourceDir,
    "--limit", $Limit,
    "--expected-files", $ExpectedFiles,
    "--strict"
)

if ($Families) {
    $preflightArgs += @("--families", $Families)
}

$preflightJson = python @preflightArgs
if ($LASTEXITCODE -ne 0) {
    throw "Preflight Python falhou com exit code $LASTEXITCODE."
}

$report = $preflightJson | ConvertFrom-Json
$preflightJson

if ($report.status -eq "fail") {
    throw "Preflight da base Receita falhou. Corrija os checks antes de importar."
}

if (!$SkipDockerCheck) {
    docker version | Out-Null
    docker compose ps $Service | Out-Null

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\apply_postgres_migrations.ps1 -Service $Service
    if ($LASTEXITCODE -ne 0) {
        throw "Aplicacao de migrations falhou com exit code $LASTEXITCODE."
    }
}

Write-Output "Preflight Receita/Postgres concluido com status: $($report.status)"
Write-Output "Smoke test sugerido: $($report.next_commands.smoke_import)"
Write-Output "Importacao completa sugerida: $($report.next_commands.snapshot_import)"
