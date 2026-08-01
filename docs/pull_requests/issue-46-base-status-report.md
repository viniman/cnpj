# PR - Issue 46: Relatório consolidado de status da base

## Contexto

A validação da base Receita/Postgres já tinha preflight, importação smoke,
contagens e gate de disco. Ainda faltava um comando único para resumir o estado
atual da base e deixar claro qual é o próximo bloqueio ou próximo passo.

Issue: #46

## Implementado

- Adicionado `scripts/plan_receita_base_status.py`.
- Adicionado `scripts/check_receita_base_status.ps1`.
- O relatório consolida snapshot, diretório, status do preflight, capacidade de
  disco, comandos recomendados e próximo gate.
- O wrapper PowerShell também valida contagens do smoke test quando o Postgres
  local está em execução.
- Adicionados testes para o planner consolidado e cobertura estática do wrapper.

## Como verificar

```powershell
python -m unittest tests.test_receita_base_status tests.test_postgres_migrations
powershell -NoProfile -Command "`$null = [scriptblock]::Create((Get-Content -Raw 'scripts\check_receita_base_status.ps1')); 'PowerShell base status script parsed'"
```

Com snapshot local:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_base_status.ps1 `
  -Snapshot 2026-07
```

## Checklist

- [x] Branch criada a partir da issue.
- [x] Nome da branch não usa prefixo de IA.
- [x] Relatório indica bloqueio de disco quando a carga completa não cabe.
- [x] Comando mostra o próximo gate operacional.
- [x] Testes automatizados adicionados.
- [x] Documentação de PR adicionada.

## Resultado validado

```text
python -m unittest tests.test_receita_base_status tests.test_postgres_migrations tests.test_receita_staging_preflight tests.test_postgres_staging tests.test_postgres_snapshot_plan
Ran 26 tests
OK

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_base_status.ps1 -Snapshot 2026-07
status: blocked_disk
recognized_files: 37
total_bytes: 7643363104
free_bytes: 6492524544
required_bytes: 22930089312
cnaes_raw: 1359
municipios_raw: 5572
naturezas_raw: 91
```

## Observações

- A carga completa da Receita continua bloqueada neste ambiente por falta de
  espaço em disco.
- A issue #41 permanece como gate aberto para validar a importação completa em
  ambiente com capacidade.
