# Fase 39 - Checkpoints de importacao oficial

## Objetivo

Permitir que a importacao automatica da base oficial da Receita seja feita em
lotes retomaveis por `snapshot` e `chunk`, sem depender de uma execucao unica
longa. A fase melhora o uso local em SQLite e prepara a migracao futura para
PostgreSQL com staging e `COPY`.

## Contexto

O sistema ja descobre snapshots oficiais, baixa arquivos de dominio e importa
um chunk limitado de Empresas/Estabelecimentos/Socios. Esse fluxo e util para
amostras, mas ainda nao e seguro para cargas maiores: se a execucao falhar ou
for interrompida, o operador precisa lembrar manualmente de onde parou.

Esta fase cria um checkpoint persistido, de leitura simples na UI e API, para
executar o mesmo chunk em fatias menores.

## Escopo

- Criar tabela de checkpoint por `snapshot + chunk`.
- Adicionar `offset` ao parser de ZIP oficial.
- Registrar `next_offset`, importados, erros, status e ultimo job.
- Permitir `resume=true` em `/api/sources/official/sync`.
- Listar checkpoints pela API interna.
- Exibir checkpoints na tela de importacao local.
- Manter compatibilidade com `mode=domains`, `mode=chunk` e `mode=full`.

## Fora do escopo desta fase

- PostgreSQL real, staging tables e `COPY`.
- Processamento em background ou worker persistente.
- Importacao nacional completa em SQLite.
- Deduplicacao avancada por arquivo bruto de Receita.
- UI de pausa/cancelamento de job em execucao.

## Modelo de dados

Nova tabela `official_import_checkpoints`:

- `snapshot`: mes oficial, por exemplo `2026-06`.
- `chunk`: numero do chunk de Empresas/Estabelecimentos/Socios.
- `status`: `pending`, `running`, `completed` ou `failed`.
- `next_offset`: quantidade de estabelecimentos ativos ja consumidos.
- `limit_per_run`: tamanho do ultimo lote solicitado.
- `imported_rows`, `error_rows`: acumulados do checkpoint.
- `last_job_id`: ultimo `import_jobs.id` associado.
- `message`: resumo operacional.
- `created_at`, `updated_at`, `finished_at`.

O offset e contado sobre estabelecimentos ativos considerados pelo parser, nao
sobre linhas brutas do CSV oficial.

## Contratos internos

`GET /api/sources/official/checkpoints`

Retorna checkpoints conhecidos, ordenados por atualizacao.

`POST /api/sources/official/sync`

Novos campos aceitos:

- `resume`: quando verdadeiro em `mode=chunk`, usa `next_offset` salvo.
- `offset`: offset explicito para uma rodada pontual.

Resposta de `mode=chunk` passa a incluir:

- `checkpoint`: estado atualizado do checkpoint.
- `imported.offset`: offset usado na rodada.
- `imported.next_offset`: proximo offset sugerido.

## Criterios de aceite

- Um primeiro lote oficial grava checkpoint com `next_offset`.
- Uma segunda chamada com `resume=true` continua a partir do checkpoint.
- Falhas de importacao registram status `failed` e mensagem.
- Checkpoints sao listaveis pela API e visiveis na tela de importacao.
- Fluxos existentes sem `resume` continuam funcionando.
