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

if (!$SourceDir) {
    $SourceDir = "data/downloads/receita/$Snapshot"
}

if (!(Test-Path $SourceDir)) {
    throw "Diretório do snapshot não encontrado: $SourceDir"
}

$planJson = python scripts/plan_postgres_staging_snapshot.py `
    --snapshot $Snapshot `
    --source-dir $SourceDir `
    --families $Families `
    --limit $Limit `
    --extract-root $ExtractRoot `
    --container-dir $ContainerDir

$plan = $planJson | ConvertFrom-Json

if (!$plan.items -or $plan.items.Count -eq 0) {
    throw "Nenhum ZIP oficial reconhecido em $SourceDir"
}

Write-Output "Importando snapshot $Snapshot com $($plan.items.Count) arquivo(s)."

$imported = 0
foreach ($item in $plan.items) {
    Write-Output "[$($imported + 1)/$($plan.items.Count)] $($item.filename) -> $($item.table)"
    & "$PSScriptRoot/import_postgres_staging_file.ps1" `
        -Snapshot $Snapshot `
        -Filename $item.filename `
        -ZipPath $item.zip_path `
        -Service $Service `
        -ExtractRoot $ExtractRoot `
        -ContainerDir $ContainerDir
    $imported += 1
}

Write-Output "Snapshot importado para staging: $Snapshot ($imported arquivo(s))."
