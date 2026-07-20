# Fase 10 - Command Center action inbox

## Objetivo

Transformar a inbox do Command Center em uma caixa de decisao acionavel,
permitindo que o operador aprove, rejeite, resolva, dispense, conclua ou
cancele itens sem sair da aba `Comando`.

Esta fase mantem o Command Center como camada de orquestracao. Ele nao cria
novas regras paralelas: cada decisao e delegada para o servico de origem ja
existente, com seus proprios guardrails.

## Escopo

- Endpoint unico para decisoes da inbox:
  - `POST /api/command-center/actions`
- Acoes suportadas:
  - `approval`: `approve`, `reject`
  - `handoff`: `resolve`, `dismiss`
  - `meeting`: `complete`, `cancel`, `no_show`
- Resposta retorna:
  - resultado da acao de origem
  - snapshot atualizado do Command Center
- UI da aba `Comando`:
  - nota de decisao
  - botoes por item conforme `source_type`
  - refresh automatico apos decisao

## Fora do escopo desta fase

- Criar reuniao a partir de handoff diretamente no Command Center.
- Editar agenda/hora/link da reuniao.
- Acoes em lote.
- Permissoes/RBAC reais.
- Confirmacao nomeada para toda decisao.

## Decisao central

O endpoint de acao do Command Center funciona como um roteador seguro. Ele
valida `source_type` e `decision`, chama o servico de origem e retorna a visao
atualizada. A regra de negocio continua no modulo original:

- aprovacao de sequencia usa `approve_sequence_step` ou `reject_sequence_step`.
- handoff usa `decide_handoff`.
- reuniao usa `update_meeting_status`.

## API

### `POST /api/command-center/actions`

Payload:

```json
{
  "source_type": "approval",
  "source_id": 1,
  "decision": "approve",
  "note": "Aprovado pelo Command Center"
}
```

Resposta:

```json
{
  "source_type": "approval",
  "source_id": 1,
  "decision": "approve",
  "result": {},
  "command_center": {}
}
```

## Criterios de aceite

- Aprovar uma pendencia `approval` pela inbox executa a mesma regra de
  aprovacao de sequencia.
- Rejeitar uma pendencia `approval` nao cria envio.
- Resolver ou dispensar `handoff` pela inbox registra `agent_actions`.
- Concluir, cancelar ou marcar `no_show` em `meeting` pela inbox atualiza lead
  e reuniao.
- A API rejeita combinacoes invalidas de `source_type` e `decision`.
- UI atualiza metrics/inbox/Kanban/feed apos cada decisao.
- Testes automatizados cobrem as tres familias de item.
