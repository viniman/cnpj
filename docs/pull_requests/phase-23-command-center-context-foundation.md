# PR local - Fase 23: Command Center context foundation

Branch: `feature/23-command-center-context-foundation`

Base local: `master`

## Objetivo

Migrar Command Center e replay por lead para o workspace ativo, garantindo que
a tela de comando reflita a empresa selecionada na topbar.

## Implementado

- Especificacao da fase em `docs/COMMAND_CENTER_CONTEXT_SPEC.md`.
- ADR-025 definindo Command Center/replay como leituras do workspace ativo.
- `lead_timeline` filtrando pelo workspace ativo.
- Metricas, inbox, Kanban e feed de atividade do Command Center usando
  `current_org_id(conn)`.
- Joins de reunioes, sequencias e agent actions protegidos por `org_id`.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Metrics contam apenas dados do workspace ativo.
- [x] Inbox nao mostra aprovacoes, handoffs ou reunioes de outro workspace.
- [x] Kanban lista apenas leads do workspace ativo.
- [x] Feed de atividade lista apenas `agent_actions` do workspace ativo.
- [x] Replay de lead de outro workspace retorna vazio.
- [x] Acao do Command Center em item de outro workspace e recusada.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_command_center
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 71 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- Governanca do agente, playbooks e auditoria ainda possuem fases proprias de
  migracao para `current_org_id(conn)`.
