# Fase 20 - Cadencias por workspace ativo

## Objetivo

Migrar cadencias, passos, jornadas de lead, fila de aprovacao e logs de acao
relacionados a cadencia para o workspace ativo do MVP local.

Esta fase fecha o fluxo operacional semi-supervisionado:

lista -> leads -> templates -> cadencia -> aprovacao humana -> envio simulado.

## Escopo

- Migrar para `current_org_id(conn)`:
  - `create_cadence`;
  - `list_cadences`;
  - `get_cadence`;
  - `enroll_cadence_from_list`;
  - `list_journeys`;
  - `prepare_next_journey_step`;
  - `list_approvals`;
  - `approve_cadence_step`;
  - `reject_cadence_step`;
  - `list_agent_actions` no contexto da cadencia.
- Validar que cadencia, lista, lead, jornada e aprovacao pertencem ao
  workspace ativo antes de qualquer acao.
- Garantir que templates usados em passos pertencam ao workspace ativo.
- Cobrir isolamento multi-workspace com testes automatizados.

## Fora do escopo desta fase

- Migrar ICP/priorizacao.
- Migrar classificacao de respostas, handoffs e reunioes.
- Envio real de e-mail.
- Agente autonomo sem aprovacao humana.
- Fila serverless/QStash.

## Decisao central

Cadencias sao uma maquina de estado operacional por workspace. O backend deve
derivar `org_id` do contexto ativo e recusar IDs de outro workspace. A UI nao
deve carregar nem acionar aprovacoes/jornadas de outra empresa interna.

## Criterios de aceite

- Cadencia criada recebe `org_id` do workspace ativo.
- Listagem e detalhe de cadencias respeitam workspace ativo.
- Inscricao em cadencia recusa lista ou cadencia de outro workspace.
- Jornadas criadas recebem `org_id` do workspace ativo.
- Preparar proximo passo recusa jornada fora do workspace ativo.
- Aprovacao, rejeicao e listagem de aprovacoes respeitam workspace ativo.
- Logs de `agent_actions` de cadencia ficam no workspace ativo.
- Testes automatizados provam isolamento entre dois workspaces.

## Implementado nesta fase

- `create_cadence`, `list_cadences` e `get_cadence` usam workspace ativo.
- Passos resolvem templates pelo workspace ativo.
- `enroll_cadence_from_list` valida lista e cadencia no workspace ativo.
- `lead_journey` nasce no workspace ativo.
- `create_step_approval`, `list_approvals`, `approve_cadence_step` e
  `reject_cadence_step` usam workspace ativo.
- `prepare_next_journey_step` recusa jornada fora do workspace ativo.
- `log_agent_action` e `list_agent_actions` usam workspace ativo.
- Campanha auxiliar de cadencia nasce no workspace ativo.
- Teste de isolamento multi-workspace em `tests/test_cadences.py`.
