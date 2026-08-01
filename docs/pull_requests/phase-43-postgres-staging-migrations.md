# PR - Fase 43: Migrations SQL do staging Postgres

Issue: https://github.com/viniman/cnpj/issues/7

## Contexto

A fase 41 criou o Postgres local e o bootstrap
`infra/postgres/init/001_bootstrap.sql`. Esta fase separa esse bootstrap de
infraestrutura das migrations reais do schema `receita_staging`.

## Mudanças

- Adicionada a primeira migration SQL timestampada do staging:
  `infra/postgres/migrations/20260801190000_create_receita_staging_raw_tables.sql`.
- Adicionado `docs/POSTGRES_MIGRATION_CONVENTIONS.md`.
- Atualizado `scripts/write_postgres_staging_sql.ps1` para concatenar
  migrations SQL em ordem.
- Atualizados testes de fundação Postgres.
- Adicionados testes de padrão e conteúdo das migrations.
- Atualizados arquitetura, roadmap, ADRs e histórico.

## Decisões

- `infra/postgres/init/001_bootstrap.sql` é bootstrap Docker, não migration de
  produto.
- Migrations SQL do staging usam `YYYYMMDDHHMMSS_descriptive_slug.sql`.
- Produto operacional futuro fica sob Prisma em
  `apps/api/prisma/migrations/<timestamp>_<slug>/migration.sql`.

## Verificação

```powershell
python -m unittest tests.test_postgres_migrations tests.test_local_postgres_foundation tests.test_postgres_staging
```
