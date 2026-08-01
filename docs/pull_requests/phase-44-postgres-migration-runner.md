# PR - Fase 44: Runner de migrations do staging Postgres

Issue: https://github.com/viniman/cnpj/issues/9

## Contexto

A fase 43 criou migrations SQL timestampadas do `receita_staging`. Esta fase
adiciona o runner local para aplicar essas migrations no Postgres Docker com
rastreabilidade.

## Mudanças

- Adicionado `scripts/apply_postgres_migrations.ps1`.
- Criado fluxo de controle em `receita_staging.schema_migrations`.
- Runner valida padrão de nome, calcula checksum SHA-256 e aplica migrations em
  ordem.
- Reaplicação com mesmo checksum é ignorada; checksum diferente falha.
- Atualizados testes, arquitetura, ADRs, convenções e histórico.

## Verificação

```powershell
python -m unittest tests.test_postgres_migrations tests.test_local_postgres_foundation
```
