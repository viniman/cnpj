# PR - Issue 29: Corrigir runner de migrations Postgres

Issue: https://github.com/viniman/cnpj/issues/29

Closes #29

## Contexto

Na primeira validação real com Docker/Postgres ativo, o runner de migrations
quebrou ao chamar `.Trim()` em retorno vazio/null da consulta de checksum. O
preflight completo também não propagava corretamente falha da aplicação de
migrations.

## Mudanças

- Normaliza `$existingChecksumResult` antes de chamar `.Trim()`.
- Faz `check_receita_staging_preflight.ps1` falhar quando
  `apply_postgres_migrations.ps1` retorna erro.
- Atualiza testes estáticos do runner e do preflight.

## Passo a Passo de Teste

1. Rodar testes focados:

```powershell
python -m unittest tests.test_postgres_migrations
```

2. Com Docker/Postgres ativo, aplicar migrations:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\apply_postgres_migrations.ps1
```

3. Rodar preflight completo:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 -Snapshot 2026-07
```

## Checklist

- [x] Runner trata checksum ausente sem `.Trim()` em null.
- [x] Preflight propaga erro de migrations.
- [x] Testes estáticos atualizados.
- [x] Migrations aplicadas no Postgres local.
- [x] Preflight completo validado com Docker/Postgres ativo.
