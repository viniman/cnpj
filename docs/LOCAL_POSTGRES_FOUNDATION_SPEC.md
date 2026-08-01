# Fase 41 - PostgreSQL local como fundacao de dados

Data: 2026-08-01

## Objetivo

Adicionar PostgreSQL real ao ambiente local para suportar a evolucao de carga
nacional da Receita Federal, mantendo o MVP Python atual funcionando em SQLite
por padrao.

Esta fase entrega:

- servico `postgres` no Docker Compose;
- variaveis padrao documentadas em `.env.example`;
- inicializacao do schema bruto `receita_staging`;
- script local para verificar disponibilidade do Postgres;
- documentacao de uso e guardrails.

## Nao objetivo

- Migrar o runtime da aplicacao Python de SQLite para PostgreSQL.
- Executar `COPY` automaticamente.
- Rodar transformacao staging -> modelo final.
- Criar NestJS ou Next.js nesta fase.

## Decisao tecnica

O projeto passa a ter dois bancos locais com papeis distintos:

- SQLite: banco operacional do MVP atual, rapido e sem dependencias.
- PostgreSQL: banco de escala para staging, carga nacional e futura API.

O Postgres deve nascer como infraestrutura real, mas opt-in. O operador pode
subir apenas o banco para preparar carga de dados, ou subir banco + aplicacao.

## Configuracao padrao

```text
POSTGRES_DB=radar_cnpj
POSTGRES_USER=radar_cnpj
POSTGRES_PASSWORD=radar_cnpj_local
POSTGRES_PORT=5432
RADAR_CNPJ_POSTGRES_DSN=postgresql://radar_cnpj:radar_cnpj_local@localhost:5432/radar_cnpj
```

## Inicializacao

O container executa SQL de `infra/postgres/init` na primeira criacao do volume.
O arquivo inicial habilita:

- `unaccent`;
- `pg_trgm`;
- schema `receita_staging`;
- tabela `schema_bootstrap_log` para registrar a versao do bootstrap.

A DDL completa das tabelas brutas continua sendo gerada pela aplicacao via
`radar_cnpj.postgres_staging`, para evitar duplicar toda a especificacao de
layout em arquivo estatico.

## Guardrails

- Nao use o usuario Postgres local em producao.
- Nao commite `.env` com senha real.
- Apague o volume Postgres local somente quando quiser reconstruir a base.
- Rode `COPY` e transformacoes longas fora do servidor HTTP local.
- Use uma instancia Postgres dedicada para snapshot nacional completo.

## Criterios de aceite

- `docker compose config` reconhece os servicos `postgres` e `radar-cnpj`.
- `.env.example` documenta as variaveis locais.
- Existe script de verificacao sem dependencia Python externa.
- Testes garantem que Compose, env e bootstrap SQL continuam alinhados.
- README, arquitetura, ADR e historico registram a fase.
