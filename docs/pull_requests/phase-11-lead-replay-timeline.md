# PR local - Fase 11: Lead replay timeline

Branch: `feature/11-lead-replay-timeline`

Base local: `master`

## Objetivo

Adicionar replay/auditoria por lead ao Command Center, permitindo reconstruir
a jornada operacional sem consultar tabelas manualmente.

## Implementado

- Especificacao da fase em `docs/LEAD_REPLAY_TIMELINE_SPEC.md`.
- ADR-013 definindo replay como composicao de leitura.
- API:
  - `GET /api/leads/{lead_id}/timeline`
- Timeline consolidada de:
  - lead e empresa
  - fila SDR/priorizacao
  - jornadas
  - aprovacoes
  - envios e eventos simulados
  - respostas classificadas
  - handoffs
  - reunioes
  - conversoes
  - `agent_actions`
- UI:
  - painel `Replay por lead` na aba `Comando`
  - campo para buscar por `lead_id`
  - botao `Replay` nos cards do Kanban
  - resumo e eventos com origem, tabela/ID e metadados expansiveis
- Testes cobrindo composicao, ordenacao e lead inexistente.

## Checklist de aceite

- [x] API retorna `404` quando o lead nao existe.
- [x] Timeline inclui aprovacao, acao do agente, resposta, handoff, reuniao e conversao.
- [x] Timeline inclui envio e evento simulado quando ha aprovacao executada.
- [x] Itens sao ordenados por `occurred_at` com desempate estavel.
- [x] Cada item possui origem, tabela/ID original e metadados.
- [x] UI carrega replay por `lead_id` sem sair do Command Center.
- [x] Testes automatizados cobrem composicao e ordenacao.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 43 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
lead_id=25
list_id=16
sequence_id=6
approval_id=7
timeline_items=21
actions=7
approvals=2
replies=1
handoffs=2
meetings=2
conversions=2
first_kind=lead
kinds=agent_action,approval,approval_decision,conversion,event,handoff,handoff_decision,journey,lead,lead_status,meeting,meeting_status,reply,send
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- A timeline nao cria tabela nova nem altera registros historicos.
- O replay ainda nao exporta PDF/CSV; isso fica para uma fase futura de
  auditoria avancada.
