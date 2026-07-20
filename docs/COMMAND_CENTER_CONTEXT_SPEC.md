# Fase 23 - Command Center e replay por workspace ativo

## Objetivo

Migrar Command Center e replay por lead para o workspace ativo. A tela de
comando deve refletir apenas metricas, inbox, Kanban, atividade e timeline do
workspace selecionado na topbar.

## Escopo

- Migrar para `current_org_id(conn)`:
  - `lead_timeline`
  - `command_center_metrics`
  - `command_center_inbox`
  - `command_center_kanban`
  - `command_center_activity`
- Validar que replay de lead fora do workspace ativo retorna vazio.
- Garantir que inbox de reunioes e Kanban nao atravessem workspaces.
- Preservar `command_center_action` delegando para servicos de origem ja
  migrados.
- Cobrir isolamento multi-workspace com testes automatizados.

## Fora do escopo desta fase

- Migrar governanca do agente, playbooks e auditoria global.
- Criar historico agregado materializado do Command Center.
- Alterar o modelo visual da UI.

## Decisao central

Command Center e replay sao composicoes de leitura, nao fontes paralelas de
verdade. Eles devem derivar o workspace ativo e ler somente tabelas do contexto
atual. Acoes continuam roteadas para os servicos de origem, que aplicam seus
proprios guardrails.

## Criterios de aceite

- Metrics do Command Center contam apenas itens do workspace ativo.
- Inbox nao mostra aprovacoes, handoffs ou reunioes de outro workspace.
- Kanban lista apenas leads do workspace ativo.
- Feed de atividade lista apenas `agent_actions` do workspace ativo.
- Replay de lead de outro workspace retorna vazio.
- `command_center_action` recusa item de outro workspace por delegacao ao
  servico de origem.
- Testes automatizados provam isolamento entre workspace interno e secundario.
