# PR - Issue 37: Gate de capacidade para carga completa

Issue: https://github.com/viniman/cnpj/issues/37

Closes #37

## Contexto

O Docker/Postgres foi ativado e o smoke import real foi validado. A carga
completa não deve ser executada no ambiente atual porque o espaço livre medido é
menor que o tamanho compactado do snapshot e insuficiente para o crescimento do
volume Postgres.

## Mudanças

- Atualiza `docs/BASE_READINESS_AUDIT.md` com smoke import real validado.
- Atualiza `docs/RECEITA_BASE_TEST_RUNBOOK.md` com gate de capacidade.
- Registra contagens reais do smoke import.
- Registra limitação de disco para full import.

## Passo a Passo de Teste

1. Conferir documentos:

```powershell
Get-Content docs\BASE_READINESS_AUDIT.md
Get-Content docs\RECEITA_BASE_TEST_RUNBOOK.md
```

2. Repetir validação do smoke import, se necessário:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas `
  -RequireData
```

## Checklist

- [x] Smoke import real marcado como validado.
- [x] Contagens reais documentadas.
- [x] Gate de disco para carga completa documentado.
- [x] Próxima ação para full import ficou explícita.
- [ ] Carga completa executada em ambiente com espaço suficiente.
