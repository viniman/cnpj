# PR - Issue 33: Importação staging idempotente

Issue: https://github.com/viniman/cnpj/issues/33

Closes #33

## Contexto

Antes da carga completa, o smoke import real mostrou que a importação precisava
ser segura para reexecução. Sem idempotência, importar o mesmo ZIP mais de uma
vez poderia duplicar linhas no `receita_staging`.

## Mudanças

- `COPY` server-side passa a carregar em tabela temporária.
- Dados anteriores do mesmo `snapshot` + `source_file` são removidos antes do
  insert.
- Metadados `snapshot`, `chunk` e `source_file` são inseridos junto dos dados.
- O `copy_sql` usado no painel também usa a estratégia idempotente.
- Testes atualizados para validar temp table, delete e insert.

## Passo a Passo de Teste

1. Rodar testes focados:

```powershell
python -m unittest tests.test_postgres_staging tests.test_postgres_snapshot_plan tests.test_receita_staging_preflight tests.test_postgres_migrations
node --check static\app.js
```

2. Reimportar o smoke import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

3. Validar contagens:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas `
  -RequireData
```

Resultado validado após reimportação:

```text
cnaes              cnaes_raw                            1359
municipios         municipios_raw                       5572
naturezas          naturezas_raw                          91
Validacao de contagens concluida.
```

## Checklist

- [x] Importação usa tabela temporária.
- [x] Reimportação remove dados antigos do mesmo snapshot/source_file.
- [x] Metadados entram no insert, sem update amplo por `source_file IS NULL`.
- [x] `copy_sql` do painel foi alinhado.
- [x] Testes automatizados atualizados.
- [x] Reimportação real do smoke import validada sem duplicar contagens.
