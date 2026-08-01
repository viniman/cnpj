# PR - Issue 50: Corrigir argumento vazio de famílias no importador completo

## Contexto

Com o gate de disco liberado, a importação completa do snapshot `2026-07`
passou no preflight, mas falhou antes de importar porque o wrapper PowerShell
enviava `--families` mesmo quando `-Families` estava vazio.

Erro observado:

```text
plan_postgres_staging_snapshot.py: error: argument --families: expected one argument
Nenhum ZIP oficial reconhecido em data/downloads/receita/2026-07
```

Issue: #50

## Implementado

- `scripts/import_postgres_staging_snapshot.ps1` agora monta `$plannerArgs`.
- `--families` só é enviado ao planner quando `-Families` tem valor.
- A importação completa sem `-Families` mantém `--limit 0` e planeja o snapshot
  completo.
- Teste estático garante que o wrapper usa argumento opcional.

## Como verificar

```powershell
python -m unittest tests.test_postgres_migrations
powershell -NoProfile -Command "`$null = [scriptblock]::Create((Get-Content -Raw 'scripts\import_postgres_staging_snapshot.ps1')); 'PowerShell snapshot import script parsed'"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 -Snapshot 2026-07 -Limit 1
```

## Checklist

- [x] Branch criada a partir da issue.
- [x] Nome da branch não usa prefixo de IA.
- [x] Argumento vazio de `--families` removido.
- [x] Smoke import com `-Families` continua suportado.
- [x] Planejamento completo sem `-Families` fica suportado.
- [x] Teste e checklist documentados.
