# Fase 15 - Notification Center proativo

## Objetivo

Criar a fundacao de notificacoes proativas do Command Center. A plataforma deve
tirar da invisibilidade eventos que exigem atencao: lead quente, campanha
pausada por risco de deliverability e OKR atingido ou em risco.

Esta fase ainda nao envia Slack, WhatsApp ou e-mail real. Ela cria a fila local,
as regras de geracao, a auditoria e a UI. Canais externos entram depois como
adaptadores sobre a mesma tabela.

## Escopo

- Modelo de dados:
  - `notifications`
- API:
  - `GET /api/notifications`
  - `POST /api/notifications/generate`
  - `POST /api/notifications/{id}/mark-read`
  - `POST /api/notifications/{id}/dismiss`
- Geracao local idempotente de notificacoes para:
  - handoffs pendentes de alta prioridade ou interesse;
  - campanhas pausadas com `pause_events` ativos;
  - key results atingidos;
  - key results em risco quando o prazo esta proximo e o progresso e baixo.
- Painel no Command Center com resumo, lista e acoes.

## Fora do escopo desta fase

- Envio real para Slack, WhatsApp, agenda ou e-mail.
- Preferencias por usuario/canal.
- Escalonamento automatico por SLA.
- Deduplicacao distribuida para ambiente multi-worker.
- Notificacoes push em tempo real.

## Decisao central

Notificacao e uma consequencia auditavel de um dado operacional, nao uma nova
fonte de verdade. Cada notificacao guarda `source_type`, `source_id` e
`metadata_json`. A acao de marcar ou dispensar nao altera o handoff, campanha ou
OKR original; apenas muda o estado da notificacao.

## Regras de geracao

### Lead quente / handoff

Gera notificacao quando existe `handoffs.status = 'pending'` e:

- `priority` e `high` ou `urgent`; ou
- `reason` indica interesse, reuniao, duvida, ambiguidade ou pessoa errada.

Tipo: `hot_lead`

### Campanha pausada

Gera notificacao para `pause_events` sem `resumed_at`.

Tipo: `campaign_paused`

### OKR atingido

Gera notificacao quando algum key result salvo tem `progress >= 100`.

Tipo: `okr_achieved`

### OKR em risco

Gera notificacao quando um objetivo salvo tem `period_end` nos proximos 14 dias
e algum key result tem `progress < 50`.

Tipo: `okr_at_risk`

## API

### `GET /api/notifications`

Resposta:

```json
{
  "summary": {"pending": 2, "sent": 0, "read": 1, "dismissed": 0},
  "items": []
}
```

### `POST /api/notifications/generate`

Executa as regras locais e retorna quantas notificacoes novas foram criadas.

### `POST /api/notifications/{id}/mark-read`

Marca a notificacao como `read`.

### `POST /api/notifications/{id}/dismiss`

Marca a notificacao como `dismissed`.

## Criterios de aceite

- Geracao cria notificacao para handoff pendente relevante.
- Geracao cria notificacao para pausa ativa de campanha.
- Geracao cria notificacoes para KR atingido e KR em risco.
- Geracao e idempotente para a mesma origem enquanto a notificacao nao foi
  dispensada.
- Acoes `mark-read` e `dismiss` atualizam status sem alterar a origem.
- UI do Command Center mostra resumo, lista e botoes de acao.
- Testes automatizados cobrem geracao, idempotencia e decisoes.
