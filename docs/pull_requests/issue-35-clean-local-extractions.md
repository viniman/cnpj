# PR - Issue 35: Limpar extrações locais após importação

Issue: https://github.com/viniman/cnpj/issues/35

Closes #35

## Contexto

A carga completa da Receita exige bastante disco. O ambiente local desta
validação tinha cerca de 6,5 GB livres no D: e 7,2 GB livres no C:, enquanto o
snapshot compactado `2026-07` tem 7,64 GB. Manter CSVs extraídos após cada
arquivo piora esse gargalo.

## Mudanças

- Remove `$manifest.extract_dir` depois de importação bem-sucedida por `ZipPath`.
- Preserva fluxos com `CsvPath` direto.
- Atualiza teste estático do importador.
- Registra a limitação de espaço no histórico.

## Passo a Passo de Teste

1. Rodar teste focado:

```powershell
python -m unittest tests.test_postgres_migrations
```

2. Rodar smoke import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

3. Conferir que a extração local foi limpa:

```powershell
Test-Path data\postgres\imports\Cnaes
Test-Path data\postgres\imports\Municipios
Test-Path data\postgres\imports\Naturezas
```

Resultado validado:

```text
False
False
False

cnaes              cnaes_raw                            1359
municipios         municipios_raw                       5572
naturezas          naturezas_raw                          91
Validacao de contagens concluida.
```

## Checklist

- [x] Extração local por ZIP é removida após sucesso.
- [x] Fluxo com `CsvPath` direto continua preservado.
- [x] Teste estático atualizado.
- [x] Smoke import real validado.
- [x] Limitação de espaço para carga completa documentada.
