# PR local - Fase 17: Workspace context foundation

Branch: `feature/17-workspace-context-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de contexto operacional por workspace no MVP local, permitindo
escolher o workspace ativo e fazer as primeiras telas de uso frequente
respeitarem esse contexto.

## Implementado

- Especificacao da fase em `docs/WORKSPACE_CONTEXT_SPEC.md`.
- ADR-019 definindo migracao gradual de dominios para `current_org_id(conn)`.
- Modelo de dados:
  - `workspace_context`
- API:
  - `GET /api/workspace-context`
  - `POST /api/workspace-context`
- Helpers backend:
  - `ensure_workspace_context`
  - `current_org_id`
  - `set_current_workspace`
  - `workspace_context`
- Dashboard calculado a partir das listas do workspace ativo.
- Listas criadas, listadas, detalhadas, editadas e exportadas no workspace
  ativo.
- Notificacoes listadas, geradas, marcadas como lidas e dispensadas no
  workspace ativo.
- OKRs/KPIs criados e listados no workspace ativo.
- Seletor de workspace na topbar da interface.
- Recarregamento contextual da visao aberta apos trocar workspace.
- Testes dedicados em `tests/test_workspace_context.py`.

## Checklist de aceite

- [x] Existe workspace ativo default quando `workspace_context` esta vazio.
- [x] Trocar workspace ativo persiste em `workspace_context`.
- [x] Dashboard reflete listas/empresas do workspace ativo.
- [x] Listas respeitam o workspace ativo.
- [x] Notificacoes respeitam o workspace ativo.
- [x] OKRs/KPIs respeitam o workspace ativo.
- [x] UI permite trocar workspace sem recarregar a pagina.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest tests.test_workspace_context
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 64 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
workspace_before=1
workspace_switch_to=2
dashboard_workspace=2
dashboard_lists=0
dashboard_companies=0
workspace_restored=1
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O contexto e singleton/local, adequado para uso em localhost.
- A tabela `companies` continua global nesta fase; empresas entram no escopo do
  dashboard por listas do workspace ativo.
- Campanhas, templates, sequencias, ICP, respostas e reunioes ainda devem ser
  migrados em fases dedicadas.
