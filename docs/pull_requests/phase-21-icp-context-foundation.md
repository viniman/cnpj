# PR local - Fase 21: ICP context foundation

Branch: `feature/21-icp-context-foundation`

Base local: `master`

## Objetivo

Migrar regras ICP e fila de priorizacao SDR para o workspace ativo, evitando
que empresas internas diferentes compartilhem regra comercial, lista ou
sugestao operacional por acidente.

## Implementado

- Especificacao da fase em `docs/ICP_CONTEXT_SPEC.md`.
- ADR-023 definindo ICP e fila SDR como dominio do workspace ativo.
- `create_icp_rule`, `get_icp_rule` e `list_icp_rules` usando
  `current_org_id(conn)`.
- Priorizacao validando regra e lista contra o workspace ativo.
- `lead_priority_queue` criada, listada e decidida por workspace ativo.
- Auditoria e `agent_actions` gravados no workspace ativo.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Regra ICP criada recebe `org_id` do workspace ativo.
- [x] Listagem e detalhe de ICP respeitam o workspace ativo.
- [x] Priorizacao recusa regra ou lista de outro workspace.
- [x] Leads auxiliares criados pela priorizacao ficam no workspace ativo.
- [x] Fila SDR mostra e decide apenas itens do workspace ativo.
- [x] Logs de `agent_actions` e auditoria da fase ficam no workspace ativo.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
python -m unittest tests.test_icp_prioritization
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 68 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Empresas continuam globais no MVP local; listas definem o escopo operacional
  de cada workspace.
- Respostas, handoffs e reunioes ainda exigem fase propria de migracao para
  `current_org_id(conn)`.
