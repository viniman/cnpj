# PR - Issue 13: Importar arquivos oficiais para staging Postgres

Issue: https://github.com/viniman/cnpj/issues/13

## Contexto

Depois das migrations e do runner do staging, esta PR adiciona o primeiro fluxo
testável para importar um arquivo oficial da Receita para `receita_staging`.

## Mudanças

- Adiciona SQL server-side para `COPY` no staging.
- Adiciona manifesto de importação com família, tabela, CSV local e caminho no
  container.
- Adiciona planner Python `scripts/plan_postgres_staging_import.py`.
- Adiciona script `scripts/import_postgres_staging_file.ps1`.
- Atualiza testes e documentação.

## Passo a Passo de Teste

1. Subir o Postgres local:

```powershell
docker compose up -d postgres
```

2. Aplicar migrations e importar um ZIP pequeno de domínio:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_file.ps1 `
  -Snapshot 2026-07 `
  -Filename Cnaes.zip `
  -ZipPath data\downloads\receita\2026-07\Cnaes.zip
```

3. Conferir a contagem:

```powershell
docker compose exec -T postgres psql -U radar_cnpj -d radar_cnpj -c "SELECT count(*) FROM receita_staging.cnaes_raw;"
```

## Checklist

- [x] Usa classificação oficial de arquivos.
- [x] Aplica migrations antes da importação.
- [x] Extrai CSV do ZIP.
- [x] Copia CSV para o container Postgres.
- [x] Executa `COPY` server-side.
- [x] Atualiza metadados `snapshot`, `chunk` e `source_file`.
- [x] Inclui testes unitários focados.
- [ ] Validação real com Docker/Postgres local ativo.

## Observação de Ambiente

Durante esta implementação, o Docker Desktop/Linux engine não estava ativo no
ambiente local usado pelo agente. Por isso, a validação real do `COPY` no
Postgres ficou como passo manual de teste. Foram validados os testes unitários,
o planner Python e o parse do script PowerShell.
