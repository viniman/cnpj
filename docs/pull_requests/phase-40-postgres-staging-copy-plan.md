# PR - Fase 40: PostgreSQL staging e plano COPY

## Objetivo

Preparar a plataforma para carga nacional da Receita Federal em PostgreSQL sem
interromper o MVP local em SQLite.

## Implementado

- Modulo `radar_cnpj.postgres_staging` para gerar DDL de staging e comandos
  `psql \copy`.
- Deteccao de familias oficiais (`Empresas`, `Estabelecimentos`, `Socios`,
  dominios e Simples).
- Endpoint `GET /api/sources/official/postgres-plan`.
- Painel na tela `Importacao` com resumo, metricas, comandos e DDL copiavel.
- Testes cobrindo classificacao de arquivos, DDL, plano COPY e rota HTTP.

## Fora do escopo

- Migracao completa do app para PostgreSQL.
- Execucao automatica de `COPY`.
- Dependencia de driver Postgres.
- Transformacao de staging para tabelas finais.

## Checklist

- [x] SQLite local continua sendo o runtime do MVP.
- [x] O plano usa apenas `source_files` e arquivos locais ja baixados.
- [x] Arquivos ausentes e indisponiveis ficam explicitos.
- [x] Comandos COPY incluem `LATIN1`, delimitador `;` e metadados de snapshot.
- [x] UI nao executa carga real automaticamente.
- [x] Documentacao registra decisao e guardrails.

## Como testar localmente

```powershell
python -m unittest tests.test_postgres_staging
node --check static\app.js
```

Para verificar pelo servidor local:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/sources/official/postgres-plan"
```
