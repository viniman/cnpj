# Fase 11 - Lead replay timeline

## Objetivo

Criar uma visao de replay/auditoria por lead para que o operador consiga
reconstruir, em ordem cronologica, tudo que aconteceu com uma empresa/lead:
priorizacao, aprovacao, envio simulado, resposta, handoff, reuniao,
conversoes e decisoes humanas.

Esta fase transforma os logs ja existentes em uma experiencia consultavel no
Command Center, sem criar nova fonte paralela de verdade.

## Escopo

- API de leitura:
  - `GET /api/leads/{lead_id}/timeline`
- Timeline consolidada a partir de:
  - `leads`
  - `companies`
  - `lead_journey`
  - `approval_queue`
  - `sends`
  - `events`
  - `reply_classifications`
  - `handoffs`
  - `meetings`
  - `conversions`
  - `agent_actions`
- UI na aba `Comando`:
  - campo para informar `lead_id`
  - cards de resumo do lead e empresa
  - linha do tempo ordenada com origem, tipo, data, titulo e motivo
- Itens de timeline sempre mostram origem/fonte:
  - regra de negocio
  - humano
  - sistema
  - CRM interno
  - evento de campanha

## Fora do escopo desta fase

- Replay visual animado passo a passo.
- Edicao de itens historicos.
- Busca textual global por lead/e-mail.
- Timeline multi-workspace real.
- Exportacao PDF/CSV da timeline.

## Decisao central

O replay e uma composicao de leitura. Ele nao duplica nem move dados para uma
tabela nova. Cada item preserva `source_table`, `source_id`, `origin_label` e
`occurred_at`, para que seja possivel voltar ao registro original.

## API

### `GET /api/leads/{lead_id}/timeline`

Resposta:

```json
{
  "lead": {},
  "company": {},
  "summary": {
    "timeline_items": 12,
    "actions": 4,
    "approvals": 1,
    "replies": 1,
    "handoffs": 1,
    "meetings": 1,
    "conversions": 2
  },
  "timeline": [
    {
      "occurred_at": "2026-07-20T04:16:50Z",
      "source_table": "agent_actions",
      "source_id": 10,
      "kind": "agent_action",
      "title": "reply_classified",
      "origin_label": "Regra de negocio",
      "detail": "Resposta classificada como interest_meeting",
      "metadata": {}
    }
  ]
}
```

## Criterios de aceite

- API retorna `404` quando o lead nao existe.
- Timeline inclui eventos de aprovacao, acao do agente, resposta, handoff,
  reuniao e conversao quando esses dados existem.
- Itens sao ordenados por `occurred_at` e desempate estavel.
- Cada item possui `source_table`, `source_id`, `kind`, `title`,
  `origin_label` e `detail`.
- UI do Command Center carrega a timeline de um `lead_id` e exibe resumo,
  empresa e eventos sem navegar para outra tela.
- Testes automatizados cobrem composicao e ordenacao.
