# PR local - Fase 20: Sequence context foundation

Branch: `feature/20-sequence-context-foundation`

Base local: `master`

## Objetivo

Migrar sequencias, jornadas, aprovacoes e logs de cadencia para o workspace
ativo, completando o fluxo semi-supervisionado por empresa interna.

## Implementado

- Especificacao da fase em `docs/SEQUENCE_CONTEXT_SPEC.md`.
- ADR-022 definindo sequencias como maquina de estado por workspace.
- `create_sequence`, `list_sequences` e `get_sequence` usando
  `current_org_id(conn)`.
- Passos de sequencia resolvendo templates no workspace ativo.
- `enroll_sequence_from_list` validando lista e sequencia no workspace ativo.
- `lead_journey` criado e listado por workspace ativo.
- `approval_queue` criada, listada, aprovada e rejeitada por workspace ativo.
- `prepare_next_journey_step` bloqueando jornada fora do workspace ativo.
- `agent_actions` de cadencia criadas e listadas por workspace ativo.
- Campanha auxiliar de sequencia criada no workspace ativo.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Sequencia criada recebe `org_id` do workspace ativo.
- [x] Listagem e detalhe de sequencias respeitam workspace ativo.
- [x] Inscricao em sequencia recusa lista ou sequencia de outro workspace.
- [x] Jornadas criadas recebem `org_id` do workspace ativo.
- [x] Preparar proximo passo recusa jornada fora do workspace ativo.
- [x] Aprovacao, rejeicao e listagem de aprovacoes respeitam workspace ativo.
- [x] Logs de `agent_actions` de sequencia ficam no workspace ativo.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
python -m unittest tests.test_sequences
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 67 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O envio continua simulado e dependente de aprovacao humana.
- ICP/priorizacao, respostas, handoffs e reunioes ainda exigem fases proprias
  de migracao para `current_org_id(conn)`.
