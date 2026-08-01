# PR - Issue 25: Runbook de teste da base Receita/Postgres

Issue: https://github.com/viniman/cnpj/issues/25

Closes #25

## Contexto

As issues recentes criaram preflight, comandos no painel e validação de
contagens. Esta PR consolida o passo a passo em um único runbook para reduzir
ambiguidade na hora de testar a base.

## Mudanças

- Adiciona `docs/RECEITA_BASE_TEST_RUNBOOK.md`.
- Consolida testes automatizados, preflight, painel, Postgres, smoke import,
  contagens e importação completa.
- Define critérios de aceite manual.
- Registra limitações atuais da base.

## Passo a Passo de Teste

1. Conferir o runbook:

```powershell
Get-Content docs\RECEITA_BASE_TEST_RUNBOOK.md
```

2. Rodar validações focadas citadas no runbook:

```powershell
python -m unittest tests.test_postgres_staging tests.test_postgres_snapshot_plan tests.test_receita_staging_preflight tests.test_postgres_migrations
node --check static\app.js
```

3. Rodar preflight sem Docker:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 `
  -Snapshot 2026-07 `
  -SkipDockerCheck
```

## Checklist

- [x] Runbook criado.
- [x] Passo a passo cobre painel interno.
- [x] Passo a passo cobre smoke import.
- [x] Passo a passo cobre contagens pós-importação.
- [x] Critérios de aceite documentados.
- [x] Limitações atuais documentadas.
- [ ] Smoke import real validado com Docker/Postgres ativo.
