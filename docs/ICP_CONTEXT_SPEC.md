# Fase 21 - ICP e priorizacao por workspace ativo

## Objetivo

Migrar regras de ICP e fila de priorizacao SDR para o workspace ativo do MVP
local. O operador deve poder trocar de workspace e criar, listar, priorizar e
decidir sugestoes sem misturar ICPs, listas ou leads de outra empresa interna.

## Escopo

- Migrar para `current_org_id(conn)`:
  - `create_icp_rule`
  - `get_icp_rule`
  - `list_icp_rules`
  - `prioritize_icp_rule`
  - `icp_candidate_rows`
  - `existing_priority_item`
  - `upsert_priority_item`
  - `list_priority_queue`
  - `decide_priority_queue_item`
- Validar que lista informada para priorizacao pertence ao workspace ativo.
- Garantir que leads criados a partir de lista nascem no workspace ativo.
- Registrar auditoria e `agent_actions` no workspace ativo.
- Provar isolamento multi-workspace com testes automatizados.

## Fora do escopo desta fase

- Migrar respostas, handoffs e reunioes.
- Criar varios ICPs ativos com pesos por playbook.
- Clonar ICPs entre workspaces.
- Implementar RBAC por usuario.

## Decisao central

ICP e uma regra operacional do workspace. A UI nao escolhe `org_id`; o backend
deriva o contexto do singleton local `workspace_context`. Qualquer ID recebido
pela API deve ser validado contra o workspace ativo antes de criar leads,
sugestoes ou decisoes humanas.

## Contratos

### Regras ICP

- Criacao grava `icp_rules.org_id` com o workspace ativo.
- Listagem retorna apenas regras do workspace ativo.
- Detalhe de regra fora do workspace ativo retorna vazio.

### Priorizacao

- `prioritize_icp_rule` recusa regra inexistente no workspace ativo.
- `prioritize_icp_rule` recusa lista de outro workspace.
- Candidatos vindos de lista usam apenas vinculos da lista validada.
- Itens de `lead_priority_queue` sao gravados com `org_id` ativo.
- Decisao humana recusa item fora do workspace ativo.

## Criterios de aceite

- Criar ICP em workspace secundario grava `org_id` correto.
- Workspace secundario nao lista, detalha, prioriza ou decide ICP/fila do
  workspace interno.
- Priorizacao com lista de outro workspace falha antes de criar leads ou itens.
- Itens priorizados e leads auxiliares ficam no workspace ativo.
- Logs de `agent_actions` da priorizacao e da decisao ficam no workspace ativo.
- Testes automatizados provam isolamento entre dois workspaces.
