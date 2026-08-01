# PR - Issue 23: Validação de contagens do staging Receita

Issue: https://github.com/viniman/cnpj/issues/23

Closes #23

## Contexto

Depois de importar um smoke test ou o snapshot completo da Receita, precisamos
de um comando padronizado para provar que as tabelas raw do `receita_staging`
receberam dados do snapshot esperado.

## Mudanças

- Adiciona `scripts/check_receita_staging_counts.ps1`.
- Permite filtrar famílias com `-Families`.
- Permite falhar quando uma tabela esperada estiver vazia com `-RequireData`.
- Consulta as tabelas raw principais do `receita_staging`.
- Atualiza documentação e testes estáticos.

## Passo a Passo de Teste

1. Validar testes e parse do script:

```powershell
python -m unittest tests.test_postgres_migrations
powershell -NoProfile -Command "`$null = [scriptblock]::Create((Get-Content -Raw 'scripts\check_receita_staging_counts.ps1')); 'PowerShell counts script parsed'"
```

2. Depois de rodar o smoke import, validar contagens dos domínios:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas `
  -RequireData
```

3. Depois da carga completa, validar todas as famílias:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -RequireData
```

## Checklist

- [x] Script consulta contagens por família/tabela.
- [x] Script permite validar smoke import por famílias.
- [x] Script pode falhar quando há tabela sem dados.
- [x] Teste estático adicionado.
- [x] Documentação operacional atualizada.
- [ ] Consulta real contra Postgres com dados importados.
