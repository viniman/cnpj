# PR - Issue 39: Capacidade de disco no preflight

Issue: https://github.com/viniman/cnpj/issues/39

Closes #39

## Contexto

O smoke import real foi validado, mas a carga completa ficou bloqueada por
capacidade de disco. Esta PR transforma esse gate documentado em validação
automática para evitar iniciar uma carga nacional em ambiente sem espaço.

## Mudanças

- Adiciona check `disk_capacity` ao JSON do preflight.
- Adiciona `--free-bytes` e `--disk-multiplier` ao planner de preflight.
- Wrapper PowerShell detecta espaço livre do drive do snapshot.
- Importador de snapshot completo chama o preflight antes de começar full import.
- Smoke/import escopado continua permitido.
- Atualiza testes e documentação.

## Passo a Passo de Teste

1. Rodar testes focados:

```powershell
python -m unittest tests.test_receita_staging_preflight tests.test_postgres_migrations
```

2. Confirmar que o full preflight falha com pouco disco:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 -Snapshot 2026-07
```

Resultado esperado neste ambiente:

```text
disk_capacity.status: fail
total_bytes: 7643363104
free_bytes: 6492880896
required_bytes: 22930089312
```

3. Confirmar que smoke/import escopado passa:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

4. Confirmar que full import é bloqueado antes de iniciar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 -Snapshot 2026-07
```

## Checklist

- [x] Preflight reporta capacidade de disco.
- [x] Full import falha com pouco espaço.
- [x] Smoke/import escopado continua permitido.
- [x] Importador completo chama preflight antes da carga.
- [x] Testes atualizados.
- [x] Documentação atualizada.
