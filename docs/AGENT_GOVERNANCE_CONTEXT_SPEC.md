# Fase 24 - Governanca do agente por workspace ativo

## Objetivo

Migrar configuracoes do agente, simulacoes e custos de IA para o workspace
ativo. Cada empresa interna deve ter sua propria versao ativa, staging,
historico de simulacao e resumo de custo.

## Escopo

- Migrar para `current_org_id(conn)`:
  - `ensure_default_agent_config`
  - `list_agent_configs`
  - `active_agent_config`
  - `next_agent_config_version`
  - `create_agent_config`
  - `activate_agent_config`
  - `list_agent_simulations`
  - `create_agent_simulation`
  - `list_agent_costs`
  - `agent_cost_summary`
  - `record_agent_cost`
  - `agent_governance`
- Validar `config_version_id` e `lead_id` contra o workspace ativo.
- Garantir que custos nao possam ser registrados em configuracao de outro
  workspace.
- Cobrir isolamento multi-workspace com testes automatizados.

## Fora do escopo desta fase

- Chamada real de LLM.
- RBAC para ativar configuracoes.
- Rollback visual na UI.
- Migrar playbooks.

## Decisao central

Governanca do agente e configuracao operacional do workspace. O default deve
ser criado separadamente por workspace quando a tela e acessada pela primeira
vez. Custos de IA tambem sao contabilizados por workspace para evitar que uma
empresa interna mascare ou inflacione o custo de outra.

## Criterios de aceite

- Workspace secundario nasce com configuracao default propria.
- Criar/ativar configuracao de outro workspace e recusado.
- Simulacao com lead de outro workspace e recusada.
- Custo com configuracao de outro workspace e recusado.
- Listagens e resumo de custo mostram apenas o workspace ativo.
- Testes automatizados provam isolamento entre workspace interno e secundario.

## Implementado nesta fase

- Defaults de agente sao criados por workspace ativo.
- `list_agent_configs`, `active_agent_config` e `activate_agent_config`
  respeitam o workspace ativo.
- Simulacoes validam configuracao e lead contra o workspace ativo.
- Custos validam configuracao, lead, cadencia e acao contra o workspace ativo.
- Listagens e resumo de custo agregam apenas o workspace ativo.
- `tests/test_agent_governance.py` cobre isolamento multi-workspace.
