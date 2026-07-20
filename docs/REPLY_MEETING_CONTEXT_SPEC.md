# Fase 22 - Respostas, handoffs e reunioes por workspace ativo

## Objetivo

Migrar respostas recebidas, handoffs humanos e reunioes para o workspace ativo.
Depois desta fase, a parte pos-resposta do fluxo SDR nao deve listar, criar,
resolver ou concluir itens de outro workspace.

## Escopo

- Migrar para `current_org_id(conn)`:
  - `record_inbound_reply`
  - `get_reply_classification`
  - `list_reply_classifications`
  - `get_handoff`
  - `list_handoffs`
  - `decide_handoff`
  - `get_meeting`
  - `create_meeting`
  - `create_meeting_from_handoff`
  - `list_meetings`
  - `update_meeting_status`
- Validar lead, send, handoff e meeting contra o workspace ativo antes de
  executar qualquer acao.
- Preservar opt-out como trilho duro: supressao continua global por e-mail.
- Garantir que conversoes e `agent_actions` gerados nesta fase fiquem no
  workspace ativo.
- Cobrir isolamento entre dois workspaces com testes automatizados.

## Fora do escopo desta fase

- Migrar replay completo por lead.
- Migrar Command Center inteiro para workspace ativo.
- Integrar calendario real.
- Criar caixa de entrada externa real por e-mail/SES receiving.

## Decisao central

Resposta, handoff e reuniao sao eventos operacionais do workspace ativo. A UI
nao envia `org_id`; o backend deriva o contexto local e recusa IDs de outro
workspace. A supressao por opt-out permanece global por seguranca, porque o
schema atual usa e-mail unico e o risco de novo contato indevido e maior que o
risco de compartilhar bloqueio entre workspaces internos.

## Criterios de aceite

- Resposta criada com `lead_id` ou `send_id` de outro workspace e recusada.
- Resposta criada no workspace ativo grava `reply_classifications.org_id`
  correto.
- Handoff criado, listado e decidido apenas no workspace ativo.
- Reuniao criada por lead ou handoff valida o workspace ativo.
- Atualizacao de status de reuniao recusa item de outro workspace.
- Conversoes e `agent_actions` desta fase ficam no workspace ativo.
- Testes automatizados provam isolamento entre workspace interno e secundario.

## Implementado nesta fase

- `reply_target` valida `send_id` por lead e campanha do workspace ativo.
- `record_inbound_reply` grava resposta, opt-out, handoff, auditoria e logs no
  workspace ativo.
- `list_reply_classifications`, `get_reply_classification`, `list_handoffs`,
  `get_handoff` e `decide_handoff` usam o workspace ativo.
- `create_meeting`, `create_meeting_from_handoff`, `list_meetings`,
  `get_meeting` e `update_meeting_status` usam o workspace ativo.
- Testes em `tests/test_reply_handoffs.py` e `tests/test_meetings.py` cobrem
  isolamento entre workspace interno e workspace secundario.
