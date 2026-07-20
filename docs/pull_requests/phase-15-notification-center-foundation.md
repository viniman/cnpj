# PR local - Fase 15: Notification center foundation

Branch: `feature/15-notification-center-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de notificacoes proativas do Command Center, com fila local,
geracao idempotente a partir de dados operacionais, acoes de leitura/dispensa e
UI dedicada.

## Implementado

- Especificacao da fase em `docs/NOTIFICATION_CENTER_SPEC.md`.
- ADR-017 definindo notificacoes como consequencias auditaveis.
- Modelo de dados:
  - `notifications`
- API:
  - `GET /api/notifications`
  - `POST /api/notifications/generate`
  - `POST /api/notifications/{id}/mark-read`
  - `POST /api/notifications/{id}/dismiss`
- Geracao local para:
  - lead quente / handoff pendente relevante;
  - campanha pausada por `pause_events`;
  - key result atingido;
  - key result em risco.
- Dedupe por `notification_type`, `source_type` e `source_id` enquanto a
  notificacao nao esta dispensada.
- Painel `Notificacoes proativas` no Command Center.
- Testes cobrindo geracao, idempotencia e atualizacao de status.

## Checklist de aceite

- [x] Geracao cria notificacao para handoff pendente relevante.
- [x] Geracao cria notificacao para pausa ativa de campanha.
- [x] Geracao cria notificacoes para KR atingido e KR em risco.
- [x] Geracao e idempotente para a mesma origem ativa.
- [x] `mark-read` e `dismiss` atualizam somente a notificacao.
- [x] UI do Command Center mostra resumo, lista e botoes de acao.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 57 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
handoff_id=8
pause_id=1
okr_id=2
generated=7
listed_total=7
pending_before_read=7
first_status_after_read=read
read_total=1
pending_after_read=6
types=campaign_paused,okr_at_risk,hot_lead,okr_achieved
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Esta fase nao envia Slack, WhatsApp ou e-mail real.
- Canais externos futuros devem consumir a mesma fila `notifications`.
