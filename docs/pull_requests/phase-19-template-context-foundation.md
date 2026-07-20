# PR local - Fase 19: Template context foundation

Branch: `feature/19-template-context-foundation`

Base local: `master`

## Objetivo

Migrar a biblioteca de templates de e-mail para o workspace ativo, garantindo
que copy, versoes e renderizacao nao atravessem empresas internas por acidente.

## Implementado

- Especificacao da fase em `docs/TEMPLATE_CONTEXT_SPEC.md`.
- ADR-021 definindo templates como configuracao operacional do workspace.
- `create_email_template` usando `current_org_id(conn)`.
- `list_email_templates` e `get_email_template` filtrando pelo workspace ativo.
- `create_email_template_version` recusando template fora do workspace ativo.
- `template_version_for_render` filtrando por workspace ativo em `template_id`
  e `template_version_id`.
- `render_email_template` auditando no workspace ativo.
- Rodape de compliance continua injetado pelo backend.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Template criado recebe `org_id` do workspace ativo.
- [x] Listagem retorna apenas templates do workspace ativo.
- [x] Detalhe de template fora do workspace ativo retorna vazio.
- [x] Nova versao so pode ser criada para template do workspace ativo.
- [x] Renderizacao recusa template ou versao de outro workspace.
- [x] Rodape de compliance continua injetado pelo backend.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
python -m unittest tests.test_email_templates
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 66 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Esta fase nao implementa compartilhamento/clonagem de templates entre
  workspaces; isso deve ser acao futura explicita e auditavel.
- Sequencias ainda usam `ORG_ID` fixo em varias funcoes e precisam de fase
  propria para completar o fluxo template -> cadencia.
