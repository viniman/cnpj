# PR - Issue 31: Corrigir argumentos opcionais do importador Postgres

Issue: https://github.com/viniman/cnpj/issues/31

Closes #31

## Contexto

Na primeira tentativa real de smoke import, o importador individual falhou porque
enviava `--csv-path` vazio para o planner Python. O `argparse` rejeitou o
argumento e o script seguiu tentando usar um manifesto nulo.

## Mudanças

- Monta argumentos do planner com `$plannerArgs`.
- Envia `--zip-path` e `--csv-path` apenas quando houver valor.
- Preserva paths Linux do container com `Container-ParentPath`.
- Propaga falhas de migrations, planner, extração, cópia para container e
  `COPY`.
- Valida manifesto vazio antes de usar paths.
- Ignora `data/postgres/`, que guarda extrações temporárias da importação.
- Atualiza testes estáticos.

## Passo a Passo de Teste

1. Rodar testes focados:

```powershell
python -m unittest tests.test_postgres_migrations
```

2. Validar parse do script:

```powershell
powershell -NoProfile -Command "`$null = [scriptblock]::Create((Get-Content -Raw 'scripts\import_postgres_staging_file.ps1')); 'PowerShell import script parsed'"
```

3. Com Docker/Postgres ativo, repetir smoke import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

4. Validar contagens do smoke import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas `
  -RequireData
```

Resultado validado:

```text
cnaes              cnaes_raw                            1359
municipios         municipios_raw                       5572
naturezas          naturezas_raw                          91
Validacao de contagens concluida.
```

## Checklist

- [x] Argumentos opcionais vazios não são enviados ao planner.
- [x] Falha do planner interrompe o script.
- [x] Manifesto vazio é tratado.
- [x] Diretório de destino no container usa path Linux.
- [x] Falhas de `COPY` são propagadas.
- [x] Extrações temporárias em `data/postgres/` não entram no Git.
- [x] Testes estáticos atualizados.
- [x] Smoke import real validado com Docker/Postgres ativo.
