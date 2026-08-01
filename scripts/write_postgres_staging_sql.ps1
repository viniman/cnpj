param(
    [string]$Output = "data/postgres/receita_staging.sql",
    [string]$MigrationsDir = "infra/postgres/migrations"
)

$ErrorActionPreference = "Stop"

$directory = Split-Path -Parent $Output
if ($directory -and !(Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory | Out-Null
}

$migrationFiles = Get-ChildItem -Path $MigrationsDir -Filter "*.sql" | Sort-Object Name
if (!$migrationFiles) {
    throw "Nenhuma migration SQL encontrada em $MigrationsDir"
}

$content = @()
foreach ($file in $migrationFiles) {
    $content += "-- migration: $($file.Name)"
    $content += Get-Content -Raw -Path $file.FullName
    $content += ""
}

$content -join "`n" | Out-File -FilePath $Output -Encoding utf8
Write-Output "Migrations PostgreSQL staging escritas em $Output"
