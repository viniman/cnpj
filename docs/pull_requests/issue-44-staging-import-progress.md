# PR - Issue 44: Progresso percentual da importação staging

Issue: https://github.com/viniman/cnpj/issues/44

Closes #44

## Contexto

O fluxo de importação por snapshot já estava funcional e seguro para smoke
import, mas a saída mostrava apenas a posição por arquivo. Para uma carga
completa com 37 arquivos, precisamos de progresso percentual e volume planejado.

## Mudanças

- Adiciona `zip_size_bytes` ao planner de snapshot.
- Mostra total planejado em bytes na importação.
- Mostra percentual por arquivos.
- Mostra percentual por bytes.
- Mantém o mesmo fluxo para smoke import e full import.
- Atualiza testes estáticos e de planner.

## Passo a Passo de Teste

1. Rodar testes focados:

```powershell
python -m unittest tests.test_postgres_snapshot_plan tests.test_postgres_migrations
```

2. Validar parse do script:

```powershell
powershell -NoProfile -Command "`$null = [scriptblock]::Create((Get-Content -Raw 'scripts\import_postgres_staging_snapshot.ps1')); 'PowerShell snapshot import script parsed'"
```

3. Rodar smoke import real:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

4. Validar contagens:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas `
  -RequireData
```

Resultado validado:

```text
[3/3 | 100,00% arquivos | 100,00% bytes] Concluido Naturezas.zip
Snapshot importado para staging: 2026-07 (3 arquivo(s), 65,51 KB).

cnaes              cnaes_raw                            1359
municipios         municipios_raw                       5572
naturezas          naturezas_raw                          91
Validacao de contagens concluida.
```

## Checklist

- [x] Script mostra progresso percentual por arquivo.
- [x] Script mostra progresso percentual por bytes.
- [x] Script mostra volume total planejado.
- [x] Planner inclui `zip_size_bytes`.
- [x] Testes atualizados.
- [x] Smoke import real validado.
