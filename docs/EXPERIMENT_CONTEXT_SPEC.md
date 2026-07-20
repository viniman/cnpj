# Fase 18 - Contexto operacional em experimentos

## Objetivo

Migrar o modulo de experimentos comerciais simulados para o workspace ativo do
MVP local. A partir desta fase, leads criados a partir de listas, campanhas,
variantes, simulacoes, eventos, supressao operacional do modulo e dashboards de
experimento devem respeitar `current_org_id(conn)`.

Esta fase continua a migracao gradual iniciada na Fase 17. O foco e fechar o
fluxo lista qualificada -> leads -> campanha simulada -> eventos/conversoes,
sem implementar envio real de e-mail.

## Escopo

- Migrar para workspace ativo:
  - `create_leads_from_list`;
  - `list_experiment_leads`;
  - `create_campaign`;
  - `list_campaigns`;
  - `get_campaign`;
  - `simulate_campaign`;
  - `record_campaign_event`;
  - `campaign_funnel`;
  - configuracao de throttle do modulo de experimento quando aplicavel.
- Garantir que campanhas de outro workspace nao sejam acessadas por detalhe,
  simulacao ou evento.
- Garantir que leads nascam com `org_id` do workspace ativo.
- Manter supressao como trilho duro por workspace ativo.
- Cobrir a migracao com testes automatizados.

## Fora do escopo desta fase

- Envio real via SES.
- Filas serverless/QStash.
- Recebimento real de webhook SNS.
- Migrar sequencias, ICP, respostas/reunioes.
- Contexto por usuario/sessao web.

## Decisao central

Experimentos devem derivar o workspace ativo do contexto local, nao de um campo
solto vindo da UI. Isso reduz risco de um operador simular campanha usando lista
de outro workspace por engano. A lista escolhida continua sendo validada no
backend contra `current_org_id(conn)`.

## Criterios de aceite

- Lead criado a partir de lista recebe `org_id` do workspace ativo.
- Listagem de leads de experimento retorna apenas leads do workspace ativo.
- Campanha criada recebe `org_id` do workspace ativo.
- Listagem e detalhe de campanhas respeitam o workspace ativo.
- Simulacao recusa lista/campanha fora do workspace ativo.
- Evento de campanha recusa envio/campanha fora do workspace ativo.
- Funil de campanha e calculado apenas para campanha do workspace ativo.
- Testes automatizados provam isolamento entre dois workspaces.

## Implementado nesta fase

- `suppression_sets` passou a consultar supressoes e opt-outs de forma global,
  respeitando o desenho atual de e-mail unico e privilegiando compliance.
- `add_suppression` audita no workspace ativo.
- `create_leads_from_list` valida a lista contra o workspace ativo e grava
  leads com esse `org_id`.
- `list_experiment_leads` filtra pelo workspace ativo.
- `create_campaign`, `list_campaigns` e `get_campaign` usam o workspace ativo.
- `simulate_campaign` recusa campanha/lista fora do workspace ativo.
- `record_campaign_event` recusa envio que nao pertence ao workspace ativo.
- Funil de campanha conta `sends` e `events` apenas da campanha no workspace
  ativo.
- A aba `Experimentos` recarrega listas ao trocar workspace.
- Templates usados para montar campanhas simuladas seguem o workspace ativo a
  partir da Fase 19.
