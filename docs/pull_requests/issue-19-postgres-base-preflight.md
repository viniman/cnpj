# PR - Issue 19: Preflight da base Receita no Postgres

Issue: https://github.com/viniman/cnpj/issues/19

Closes #19

## Contexto

As issues #13 e #17 criaram a importação de arquivo individual e de snapshot
completo. Esta PR adiciona um preflight para validar se o snapshot da Receita
está pronto antes de iniciar uma carga grande no Postgres staging.

## Mudanças

- Adiciona `scripts/plan_receita_staging_preflight.py`.
- Adiciona `scripts/check_receita_staging_preflight.ps1`.
- Valida diretório do snapshot, ZIPs oficiais, famílias obrigatórias e contagem
  esperada.
- Executa o planner de snapshot para confirmar geração de manifests.
- Exibe comandos sugeridos para migrations, smoke test e importação completa.
- Atualiza documentação e testes.

## Passo a Passo de Teste

1. Validar testes unitários e estáticos:

```powershell
python -m unittest tests.test_receita_staging_preflight tests.test_postgres_snapshot_plan tests.test_postgres_migrations
powershell -NoProfile -Command "`$null = [scriptblock]::Create((Get-Content -Raw 'scripts\check_receita_staging_preflight.ps1')); 'PowerShell preflight script parsed'"
```

2. Validar preflight contra a base local já baixada:

```powershell
python scripts\plan_receita_staging_preflight.py `
  --snapshot 2026-07 `
  --source-dir data\downloads\receita\2026-07 `
  --strict
```

3. Validar wrapper PowerShell sem Docker:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 `
  -Snapshot 2026-07 `
  -SkipDockerCheck
```

4. Quando o Docker Desktop estiver ativo, validar também Postgres e migrations:

```powershell
docker compose up -d postgres
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 `
  -Snapshot 2026-07
```

## Checklist

- [x] Cria relatório JSON de preflight.
- [x] Valida 37 ZIPs reconhecidos no snapshot `2026-07`.
- [x] Confere famílias obrigatórias da Receita.
- [x] Confirma que o planner gera 37 manifests.
- [x] Wrapper PowerShell permite uso com e sem Docker.
- [x] Testes unitários adicionados.
- [x] Documentação operacional atualizada.
- [ ] Validação real com Docker/Postgres ativo.
