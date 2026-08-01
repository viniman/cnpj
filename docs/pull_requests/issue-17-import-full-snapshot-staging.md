# PR - Issue 17: Importar snapshot completo para staging Postgres

Issue: https://github.com/viniman/cnpj/issues/17

## Contexto

A issue #13 criou importação de arquivo individual. Esta PR cria o fluxo de
snapshot, que percorre os ZIPs reconhecidos de um mês e chama o importador de
arquivo para cada item.

## Mudanças

- Adiciona planner `scripts/plan_postgres_staging_snapshot.py`.
- Adiciona script `scripts/import_postgres_staging_snapshot.ps1`.
- Ordena arquivos por família e chunk.
- Permite smoke test com `-Families` e `-Limit`.
- Atualiza testes e documentação.

## Passo a Passo de Teste

1. Subir Postgres:

```powershell
docker compose up -d postgres
```

2. Importar só domínios para smoke test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

3. Conferir contagens:

```powershell
docker compose exec -T postgres psql -U radar_cnpj -d radar_cnpj -c "SELECT count(*) FROM receita_staging.cnaes_raw;"
```

4. Importar snapshot completo:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 -Snapshot 2026-07
```

## Checklist

- [x] Lista somente ZIPs oficiais reconhecidos.
- [x] Ordena execução por família/chunk.
- [x] Permite smoke test por famílias.
- [x] Reusa o importador de arquivo individual.
- [x] Inclui testes unitários focados.
- [ ] Validação real com Docker/Postgres local ativo.
