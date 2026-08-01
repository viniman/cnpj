param(
    [string]$Service = "postgres"
)

$ErrorActionPreference = "Stop"

$containerId = docker compose ps -q $Service
if (-not $containerId) {
    throw "Servico '$Service' nao esta rodando. Use: docker compose up -d postgres"
}

$postgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "radar_cnpj" }
$postgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "radar_cnpj" }

docker compose exec -T $Service pg_isready -U $postgresUser -d $postgresDb
docker compose exec -T $Service psql -U $postgresUser -d $postgresDb -c "SELECT version();"
docker compose exec -T $Service psql -U $postgresUser -d $postgresDb -c "SELECT extname FROM pg_extension WHERE extname IN ('unaccent', 'pg_trgm') ORDER BY extname;"
docker compose exec -T $Service psql -U $postgresUser -d $postgresDb -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'receita_staging';"
