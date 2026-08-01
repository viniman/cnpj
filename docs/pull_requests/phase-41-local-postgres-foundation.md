# PR - Fase 41: PostgreSQL local como fundacao

## Objetivo

Adicionar PostgreSQL real ao ambiente local para preparar carga nacional da
Receita, sem migrar o runtime Python atual de SQLite.

## Implementado

- Servico `postgres` no `docker-compose.yml` com PostgreSQL 16 Alpine.
- Volume persistente `postgres-data`.
- Healthcheck com `pg_isready`.
- `.env.example` com variaveis SQLite e Postgres.
- Bootstrap SQL em `infra/postgres/init/001_bootstrap.sql`.
- Script `scripts/check_postgres.ps1` para verificar banco, extensoes e schema.
- Script `scripts/write_postgres_staging_sql.ps1` para gerar a DDL completa de
  staging a partir do modulo Python.
- Testes para Compose, env, bootstrap SQL e scripts.

## Fora do escopo

- Conectar a aplicacao Python ao Postgres.
- Executar `COPY` automaticamente.
- Rodar transformacao staging -> modelo final.
- Criar NestJS ou Next.js.

## Checklist

- [x] SQLite continua sendo o banco do MVP local.
- [x] Postgres sobe como infraestrutura real no Docker Compose.
- [x] Extensoes `unaccent` e `pg_trgm` sao inicializadas.
- [x] Schema `receita_staging` nasce no bootstrap.
- [x] Testes nao dependem de Docker rodando.
- [x] Scripts operacionais documentam verificacao e DDL.

## Como testar localmente

```powershell
python -m unittest tests.test_local_postgres_foundation
docker compose config --services
docker compose up -d postgres
.\scripts\check_postgres.ps1
.\scripts\write_postgres_staging_sql.ps1
```

Em Windows com politica local bloqueando scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_postgres.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\write_postgres_staging_sql.ps1
```
