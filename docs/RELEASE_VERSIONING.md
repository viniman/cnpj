# Versionamento e fechamento da base inicial

Este projeto deve usar issues, PRs e releases semânticas como trilho principal
de evolução. A numeração de fases fica preservada apenas como histórico inicial.

## Regra principal

- Toda mudança relevante começa em uma issue.
- A branch usa o número da issue e um slug semântico.
- A PR fecha ou avança uma issue clara.
- O corpo da PR inclui objetivo, mudanças, testes, checklist e riscos.
- Commits seguem Conventional Commits.
- Tags de release seguem `vMAJOR.MINOR.PATCH`.
- Branches, commits e PRs não devem usar prefixos, sufixos ou coautoria de
  ferramenta, IA, agente ou fornecedor.

Exemplos:

```text
feature/52-company-search-api
fix/53-postgres-copy-encoding
docs/54-release-runbook
```

## Versões semânticas

Enquanto o produto estiver em uso interno e ainda sem contrato público maduro,
as versões devem ficar em `v0.x.y`.

- `PATCH`: correções compatíveis, ajustes de documentação e pequenos reparos.
- `MINOR`: novas capacidades compatíveis, como um novo módulo, API ou fluxo de
  importação validado.
- `MAJOR`: mudanças incompatíveis em contrato público, banco operacional ou API
  madura.

## Primeira release esperada: v0.1.0

A release `v0.1.0` deve representar a base inicial Receita/Postgres pronta para
teste operacional interno.

Ela só deve ser criada depois da PR final de fechamento da base inicial.

## Checklist obrigatório da v0.1.0

- [ ] Issue #41 concluída com importação completa em ambiente com capacidade.
- [ ] Snapshot oficial reconhecido com 37 arquivos.
- [ ] Preflight completo sem falhas.
- [ ] Migrations Postgres aplicadas sem drift de checksum.
- [ ] Smoke import validado.
- [ ] Importação completa validada.
- [ ] Contagens completas maiores que zero para todas as famílias.
- [ ] Runbook `docs/RECEITA_BASE_TEST_RUNBOOK.md` atualizado.
- [ ] Auditoria `docs/BASE_READINESS_AUDIT.md` atualizada.
- [ ] PR final de fechamento da base mergeada em `main`.
- [ ] Tag `v0.1.0` criada a partir do commit mergeado.
- [ ] Release notes publicadas no GitHub.

## Comandos de fechamento

Depois da PR final ser mergeada em `main`:

```powershell
git switch main
git pull --ff-only
git tag -a v0.1.0 -m "v0.1.0 - base inicial Receita/Postgres"
git push origin v0.1.0
```

Release notes sugeridas:

```text
v0.1.0 - Base inicial Receita/Postgres

- Importação oficial da Receita para Postgres staging.
- Preflight de snapshot, disco, Docker e migrations.
- Importação smoke e completa por script.
- Validação de contagens por família.
- Runbook de teste operacional.
- Histórico inicial de issues, PRs e decisões.
```

## Depois da v0.1.0

Depois da base inicial, o projeto deve parar de criar documentos por fases
sequenciais. A documentação nova deve ser organizada por:

- domínio de produto;
- módulo técnico;
- decisão arquitetural;
- operação/runbook;
- contrato de API;
- modelo de dados;
- release.

Esse padrão evita centenas de fases com pouco significado e mantém o histórico
útil para desenvolvimento, produto e operação.
