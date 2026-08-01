# PR - Issue 27: Auditoria de readiness da base

Issue: https://github.com/viniman/cnpj/issues/27

Closes #27

## Contexto

As PRs recentes deixaram a base Receita/Postgres pronta para teste operacional,
mas a importação real ainda depende do Docker Desktop/Linux engine estar ativo.
Esta PR consolida evidências atuais e define os gates que faltam antes da PR
final de fechamento da base.

## Mudanças

- Adiciona `docs/BASE_READINESS_AUDIT.md`.
- Registra evidências de preflight, snapshot local, planner e testes focados.
- Lista issues/PRs que compõem a base testável.
- Define gates objetivos para a PR final.
- Sugere a primeira versão semântica `v0.1.0` após validação real.

## Passo a Passo de Teste

1. Conferir auditoria:

```powershell
Get-Content docs\BASE_READINESS_AUDIT.md
```

2. Repetir validações registradas:

```powershell
python -m unittest tests.test_postgres_staging tests.test_postgres_snapshot_plan tests.test_receita_staging_preflight tests.test_postgres_migrations
node --check static\app.js
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 -Snapshot 2026-07 -SkipDockerCheck
```

## Checklist

- [x] Evidências atuais documentadas.
- [x] Relação de issues/PRs registrada.
- [x] Gates pendentes definidos.
- [x] Versão semântica inicial sugerida.
- [x] Próximas issues recomendadas.
- [ ] Smoke import real validado com Docker/Postgres ativo.
