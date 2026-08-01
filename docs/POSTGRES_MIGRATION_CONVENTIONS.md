# Convenções de migrations PostgreSQL

Este projeto separa **bootstrap de infraestrutura**, **migrations SQL de
staging** e **migrations Prisma de produto**. Essa separação evita misturar
preparo local do Docker com evolução real de schema.

## Bootstrap Docker

Arquivos em `infra/postgres/init/` são executados automaticamente pelo entrypoint
oficial do Postgres somente quando o volume nasce vazio.

Exemplo atual:

```text
infra/postgres/init/001_bootstrap.sql
```

Responsabilidade:

- habilitar extensões necessárias, como `unaccent` e `pg_trgm`;
- criar schemas mínimos, como `receita_staging`;
- registrar bootstrap local;
- preparar o terreno para migrations reais.

Esse arquivo não é migration de produto e não deve carregar tabelas
operacionais. O prefixo `001_` é aceitável aqui porque esse diretório é uma
sequência de inicialização do container, não o histórico versionado do schema.

## Migrations SQL do staging

Arquivos em `infra/postgres/migrations/` são migrations reais do schema bruto da
Receita Federal. O padrão de nome deve ser:

```text
YYYYMMDDHHMMSS_descriptive_slug.sql
```

Exemplo:

```text
infra/postgres/migrations/20260801190000_create_receita_staging_raw_tables.sql
```

Responsabilidade:

- criar tabelas brutas do `receita_staging`;
- criar índices de staging;
- manter colunas próximas ao layout oficial da Receita;
- permanecer idempotente sempre que possível com `IF NOT EXISTS`;
- não criar tabelas de produto, billing, CRM ou usuário final.

Esse padrão é próximo ao estilo do Prisma, que usa diretórios timestampados em
`prisma/migrations/<timestamp>_<slug>/migration.sql`. A diferença é que, para
staging SQL puro, usamos um arquivo `.sql` timestampado diretamente.

## Migrations Prisma do produto

Quando o backend NestJS existir, Prisma deve ser dono dos schemas operacionais
de produto, como `app`, `billing` e parte de `audit`.

Formato esperado:

```text
apps/api/prisma/migrations/20260801193000_init/migration.sql
apps/api/prisma/migrations/20260801200000_create_companies/migration.sql
```

Responsabilidade:

- usuários, workspaces, permissões e autenticação;
- empresas normalizadas e listas;
- leads, cadências, templates, CRM e campanhas;
- API keys, planos, créditos e billing;
- tabelas operacionais de auditoria.

## Regra de ownership

- `infra/postgres/init/`: bootstrap local de infraestrutura.
- `infra/postgres/migrations/`: staging bruto da Receita.
- `apps/api/prisma/migrations/`: produto operacional em NestJS/Prisma.

Python pode executar ETL e ler/escrever staging, mas não deve criar schema
operacional ad hoc. NestJS/Prisma deve concentrar as regras e migrations do
produto.
