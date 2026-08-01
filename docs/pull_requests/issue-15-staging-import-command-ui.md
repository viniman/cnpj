# PR - Issue 15: Comando de importação staging no super admin

Issue: https://github.com/viniman/cnpj/issues/15

## Contexto

A issue #13 criou o script `scripts/import_postgres_staging_file.ps1`. Esta PR
leva esse comando para o plano PostgreSQL do super admin, para que cada arquivo
baixado tenha um comando direto de importação.

## Mudanças

- Adiciona `import_command` ao plano PostgreSQL por arquivo.
- Atualiza a UI para copiar o comando direto de importação.
- Mantém extração + SQL COPY como fallback.
- Atualiza testes do plano Postgres.

## Passo a Passo de Teste

1. Rodar o servidor local.
2. Abrir a aba `Importação`.
3. Informar um snapshot com arquivos baixados, por exemplo `2026-07`.
4. Clicar em `Gerar plano`.
5. Clicar em `Copiar importação` em um arquivo pequeno, como `Cnaes.zip`.
6. Conferir que o clipboard contém `scripts\import_postgres_staging_file.ps1`.

## Checklist

- [x] Plano inclui comando direto por arquivo.
- [x] UI copia o comando novo.
- [x] Fallback antigo de extração/COPY continua disponível.
- [x] Teste unitário cobre o comando gerado.
