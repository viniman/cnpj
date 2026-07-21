# PR local - Fase 39: Checkpoints de importacao oficial

## Objetivo

Permitir que a importacao automatica da base oficial da Receita rode em lotes
retomaveis por snapshot/chunk, reduzindo retrabalho em cargas locais maiores e
preparando o caminho para PostgreSQL/staging.

## Implementado

- [x] Documento `docs/OFFICIAL_IMPORT_CHECKPOINT_SPEC.md`.
- [x] ADR sobre checkpoints antes da migracao para Postgres.
- [x] Tabela `official_import_checkpoints`.
- [x] Parser oficial com suporte a `offset`.
- [x] Importacao oficial retornando `offset`, `next_offset` e fim de chunk.
- [x] Checkpoint persistido com acumulados, status e ultimo job.
- [x] `resume=true` em `/api/sources/official/sync`.
- [x] Endpoint `GET /api/sources/official/checkpoints`.
- [x] UI local na aba `Importacao` para listar e retomar checkpoints.
- [x] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_official_sources tests.test_official_import_checkpoints
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [x] Primeiro lote oficial grava checkpoint com `next_offset`.
- [x] Segunda chamada com `resume=true` continua a partir do checkpoint.
- [x] Checkpoint concluido e detectado quando nao ha mais linhas no lote.
- [x] Checkpoints sao listaveis pela API.
- [x] Tela de importacao mostra checkpoints e acao de retomar.
- [x] Fluxos existentes sem `resume` continuam suportados.

## Verificacao realizada

Pendente ate a execucao final da fase.
