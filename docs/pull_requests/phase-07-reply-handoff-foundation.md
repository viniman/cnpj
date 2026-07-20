# PR local - Fase 07: Reply handoff foundation

Branch: `feature/07-reply-handoff-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de classificacao de respostas recebidas e handoff humano,
mantendo opt-out como trilho duro de compliance e impedindo que o conteudo da
resposta vire instrucao do sistema.

## Implementado

- Especificacao da fase em `docs/REPLY_HANDOFF_SPEC.md`.
- ADR-009 definindo respostas como dado nao confiavel.
- Tabelas:
  - `reply_classifications`
  - `handoffs`
- Servicos:
  - classificar resposta em categorias fixas
  - resolver lead por `send_id`, `lead_id` ou e-mail
  - registrar evento/conversao de resposta quando houver envio
  - suprimir opt-out imediatamente
  - parar jornadas ativas
  - criar handoff
  - resolver ou dispensar handoff
- API:
  - `POST /api/replies/classify`
  - `GET /api/replies`
  - `GET /api/handoffs`
  - `POST /api/handoffs/{id}/resolve`
  - `POST /api/handoffs/{id}/dismiss`
- UI:
  - nova aba `Respostas`
  - formulario para simular resposta recebida
  - tabela de handoffs pendentes
  - tabela de respostas classificadas
  - resolver/dispensar handoff com nota

## Checklist de aceite

- [x] Opt-out em resposta cria supressao imediata.
- [x] Opt-out para jornada ativa e atualiza lead.
- [x] Interesse claro cria handoff de alta prioridade.
- [x] Resposta ambigua cria handoff, sem acao silenciosa.
- [x] Recusa clara desqualifica lead sem novo envio.
- [x] Handoff pode ser resolvido ou dispensado com nota.
- [x] Classificacoes e decisoes registram `agent_actions`.
- [x] Testes automatizados cobrem opt-out, interesse, ambiguidade e handoff.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
```

Resultado esperado:

```text
Ran 34 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Crie ou simule um envio.
3. Abra `Respostas`.
4. Informe o `send_id` e cole uma resposta.
5. Classifique.
6. Resolva ou dispense o handoff pendente.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Esta fase ainda nao recebe e-mail real via SES.
- Opt-out e executado automaticamente; demais casos ficam para humano.

## Smoke HTTP

```text
health=True
company_email=comercial@prismafin.com.br
leads_eligible=1
reply_id=1
classification=interest_meeting
handoff_id=1
handoff_priority=high
handoff_status_after_resolve=resolved
agent_actions_total=11
```
