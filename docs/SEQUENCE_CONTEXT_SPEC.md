# Fase 20 - Sequencias por workspace ativo

## Objetivo

Migrar sequencias, passos, jornadas de lead, fila de aprovacao e logs de acao
relacionados a cadencia para o workspace ativo do MVP local.

Esta fase fecha o fluxo operacional semi-supervisionado:

lista -> leads -> templates -> sequencia -> aprovacao humana -> envio simulado.

## Escopo

- Migrar para `current_org_id(conn)`:
  - `create_sequence`;
  - `list_sequences`;
  - `get_sequence`;
  - `enroll_sequence_from_list`;
  - `list_journeys`;
  - `prepare_next_journey_step`;
  - `list_approvals`;
  - `approve_sequence_step`;
  - `reject_sequence_step`;
  - `list_agent_actions` no contexto da cadencia.
- Validar que sequencia, lista, lead, jornada e aprovacao pertencem ao
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

Sequencias sao uma maquina de estado operacional por workspace. O backend deve
derivar `org_id` do contexto ativo e recusar IDs de outro workspace. A UI nao
deve carregar nem acionar aprovacoes/jornadas de outra empresa interna.

## Criterios de aceite

- Sequencia criada recebe `org_id` do workspace ativo.
- Listagem e detalhe de sequencias respeitam workspace ativo.
- Inscricao em sequencia recusa lista ou sequencia de outro workspace.
- Jornadas criadas recebem `org_id` do workspace ativo.
- Preparar proximo passo recusa jornada fora do workspace ativo.
- Aprovacao, rejeicao e listagem de aprovacoes respeitam workspace ativo.
- Logs de `agent_actions` de sequencia ficam no workspace ativo.
- Testes automatizados provam isolamento entre dois workspaces.
