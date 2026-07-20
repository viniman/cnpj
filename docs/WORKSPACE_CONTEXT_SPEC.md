# Fase 17 - Contexto operacional por workspace

## Objetivo

Criar a fundacao para trocar o workspace operacional do MVP local. O operador
deve conseguir escolher qual workspace esta ativo e ver listas, dashboard e
notificacoes respeitando esse contexto.

Esta fase nao remove todos os usos de `ORG_ID` fixo. Ela cria o mecanismo de
contexto ativo e migra as primeiras superficies de alto uso. As proximas fases
devem migrar modulos por dominio, uma a uma.

## Escopo

- Modelo de dados:
  - `workspace_context`
- API:
  - `GET /api/workspace-context`
  - `POST /api/workspace-context`
- Persistencia do workspace ativo local.
- Helper backend para descobrir `current_org_id`.
- Migrar para contexto ativo:
  - dashboard local;
  - listas;
  - notificacoes;
  - criacao de listas;
  - auditoria dessas operacoes iniciais.
- UI:
  - seletor de workspace na topbar;
  - recarregar telas contextuais ao trocar workspace;
  - sinal visual do workspace ativo.

## Fora do escopo desta fase

- Login/RBAC por usuario.
- Migrar empresas brutas para `org_id`.
- Migrar todos os modulos de campanha, agente, templates e ICP de uma vez.
- Troca de workspace por URL ou sessao multiusuario.
- Isolamento forte de dados sensiveis para SaaS publico.

## Decisao central

O MVP local ganha um unico workspace ativo persistido no banco. Endpoints ja
migrados leem `current_org_id(conn)`. Endpoints ainda nao migrados continuam no
workspace interno ate suas fases dedicadas. A UI deve ser clara: trocar
workspace altera as superficies migradas agora, e a documentacao lista esse
limite.

## API

### `GET /api/workspace-context`

Resposta:

```json
{
  "active_workspace": {},
  "workspaces": [],
  "updated_at": "2026-07-20T05:26:42Z"
}
```

### `POST /api/workspace-context`

Payload:

```json
{"org_id": 2}
```

Define o workspace ativo local.

## Implementado nesta fase

- Tabela singleton `workspace_context`.
- Helpers `ensure_workspace_context`, `current_org_id`,
  `set_current_workspace` e `workspace_context`.
- Endpoints:
  - `GET /api/workspace-context`
  - `POST /api/workspace-context`
- Dashboard local agora calcula empresas a partir das listas do workspace
  ativo e retorna `active_workspace`.
- Listas criadas, listadas, detalhadas, exportadas e editadas usam o workspace
  ativo.
- Notificacoes listadas, geradas, lidas e dispensadas usam o workspace ativo.
- OKRs/KPIs criados e listados usam o workspace ativo nas metricas migradas.
- A topbar tem seletor de workspace e recarrega a visao aberta apos troca.

## Limites conhecidos

- A tabela `companies` continua global nesta fase; o dashboard conta empresas
  por vinculo em listas do workspace.
- Playbooks e auditoria ainda mantem migracoes dedicadas para fases futuras.
  Experimentos/campanhas simuladas foram migrados na Fase 18; templates de
  e-mail foram migrados na Fase 19;
  sequencias/jornadas/aprovacoes foram migradas na Fase 20; ICP e fila SDR
  foram migrados na Fase 21; respostas, handoffs e reunioes foram migrados na
  Fase 22; Command Center e replay foram migrados na Fase 23; governanca do
  agente e custos foram migrados na Fase 24.
- O contexto e local/singleton, adequado para localhost. Produto SaaS exigira
  contexto por usuario/sessao e RBAC.

## Criterios de aceite

- Existe workspace ativo default quando a tabela esta vazia.
- Trocar workspace ativo persiste em `workspace_context`.
- Dashboard usa o workspace ativo para listas, leads, handoffs,
  notificacoes e custo de IA onde a metrica ja possui `org_id`; empresas sao
  medidas por listas.
- Listas criadas e listadas usam o workspace ativo.
- Notificacoes listadas e geradas usam o workspace ativo.
- OKRs e KPIs migrados usam o workspace ativo.
- UI permite trocar workspace e recarrega dashboard/listas/comando.
- Testes automatizados cobrem contexto default, troca e superficies migradas.
