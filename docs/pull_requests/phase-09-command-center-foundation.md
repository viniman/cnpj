# PR local - Fase 09: Command Center foundation

Branch: `feature/09-command-center-foundation`

Base local: `master`

## Objetivo

Criar a primeira versao do Centro de Comando operacional, agregando pendencias
humanas, CRM Kanban e feed de atividade sem substituir as fontes de verdade dos
modulos existentes.

## Implementado

- Especificacao da fase em `docs/COMMAND_CENTER_SPEC.md`.
- ADR-011 definindo que Command Center agrega dados, nao substitui tabelas de
  origem.
- API `GET /api/command-center` com:
  - `metrics`
  - `inbox`
  - `kanban`
  - `activity`
- Inbox unificada lendo:
  - `approval_queue`
  - `handoffs`
  - `meetings`
- Kanban CRM lendo `leads` e ultimo `lead_journey`.
- Feed de atividade lendo `agent_actions`.
- Aba `Comando` no frontend local.
- CSS dedicado para o Kanban operacional.

## Checklist de aceite

- [x] API agrega aprovacoes, handoffs e reunioes sem duplicar dados.
- [x] Cada item da inbox preserva `source_type` e `source_id`.
- [x] Feed mostra origem e motivo das acoes.
- [x] Kanban mostra leads por estado com empresa/e-mail.
- [x] UI carrega o Command Center em aba propria.
- [x] Testes automatizados cobrem inbox, kanban e feed.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 38 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Crie pelo menos uma aprovacao, um handoff ou uma reuniao.
3. Abra `Comando`.
4. Confirme metricas, inbox, Kanban e feed.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Acoes ainda sao executadas nas telas de origem.
- Esta fase nao cria novas tabelas de governanca.

## Smoke HTTP

```text
health=True
company_email=dados@axisanalytics.com.br
approvals_created=1
lead_id=21
handoff_id=4
meeting_id=2
metrics_pending_approvals=2
metrics_pending_handoffs=2
metrics_open_meetings=1
inbox_source_types=approval,handoff,meeting
kanban_columns=7
kanban_cards=14
activity_items=22
```
