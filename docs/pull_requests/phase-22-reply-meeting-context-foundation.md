# PR local - Fase 22: Reply and meeting context foundation

Branch: `feature/22-reply-meeting-context-foundation`

Base local: `master`

## Objetivo

Migrar respostas, handoffs e reunioes para o workspace ativo, fechando o trecho
do fluxo SDR em que uma resposta recebida vira decisao humana e agenda
operacional.

## Implementado

- Especificacao da fase em `docs/REPLY_MEETING_CONTEXT_SPEC.md`.
- ADR-024 definindo respostas, handoffs e reunioes como dominio do workspace
  ativo.
- `reply_target` validando `send_id` por lead e campanha do workspace ativo.
- `record_inbound_reply` gravando resposta, handoff, auditoria e logs no
  workspace ativo.
- Handoffs listados e decididos por workspace ativo.
- Reunioes criadas, listadas e atualizadas por workspace ativo.
- Testes automatizados de isolamento multi-workspace.

## Checklist de aceite

- [x] Resposta por `send_id` de outro workspace e recusada.
- [x] Resposta por `lead_id` de outro workspace e recusada.
- [x] Resposta criada grava `reply_classifications.org_id` ativo.
- [x] Handoff criado/listado/decidido respeita workspace ativo.
- [x] Reuniao por lead ou handoff valida workspace ativo.
- [x] Status de reuniao de outro workspace e recusado.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
python -m unittest tests.test_reply_handoffs tests.test_meetings
python -m unittest tests.test_command_center
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 70 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Supressao e opt-out continuam globais por e-mail por seguranca.
- Replay e Command Center completo ainda possuem usos remanescentes de
  `ORG_ID` e devem ter fases futuras de refinamento.
