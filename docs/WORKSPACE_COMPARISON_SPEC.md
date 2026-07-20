# Fase 16 - Comparacao executiva multi-workspace

## Objetivo

Criar a fundacao de comparacao executiva entre workspaces/empresas. O operador
deve conseguir cadastrar workspaces internos como Real Grana, Nine ou Vagou e
ver uma tabela comparavel de metricas essenciais.

Esta fase nao converte todos os modulos para selecao dinamica de tenant. O MVP
local ainda opera principalmente no `org_id = 1`, mas a comparacao passa a ler
metricas por `org_id`, registrar snapshots e preparar a futura migracao para
multi-tenancy real.

## Escopo

- Modelo de dados:
  - `workspace_metric_snapshots`
- API:
  - `GET /api/workspaces/comparison`
  - `POST /api/workspaces`
  - `POST /api/workspaces/{id}/snapshot`
- Criacao de workspace com `organizations` e `company_profiles`.
- Calculo comparavel por workspace:
  - empresas;
  - leads ativos;
  - respostas;
  - handoffs pendentes;
  - reunioes abertas/concluidas;
  - notificacoes pendentes;
  - chamadas e custo estimado de IA.
- Snapshot executivo manual para guardar o estado comparavel no tempo.
- Painel no Command Center com cadastro, tabela e snapshots recentes.

## Fora do escopo desta fase

- Troca de workspace na aplicacao inteira.
- Autenticacao/RBAC por workspace.
- Migrar todos os servicos para receber `org_id` dinamico.
- Importacao de CNPJ isolada por workspace.
- Grafico historico visual com tendencias.

## Decisao central

Comparacao executiva pode nascer antes do multi-tenant completo, desde que seja
honesta: ela le dados agrupados por `org_id` e mostra workspaces sem dados como
zero. Isso permite preparar o produto para varias empresas sem arriscar uma
reescrita grande no meio do MVP local.

## API

### `GET /api/workspaces/comparison`

Resposta:

```json
{
  "workspaces": [],
  "snapshots": []
}
```

### `POST /api/workspaces`

Payload:

```json
{
  "name": "Nine",
  "vertical": "servicos locais",
  "default_tone": "direto, acolhedor",
  "sender_name": "Time Nine",
  "brand_color": "#2458d3"
}
```

### `POST /api/workspaces/{id}/snapshot`

Cria um snapshot das metricas executivas do workspace informado.

## Criterios de aceite

- Criar workspace gera registro em `organizations` e `company_profiles`.
- Comparacao retorna todos os workspaces com metricas calculadas.
- Workspace sem dados aparece com metricas zeradas, sem quebrar dashboard.
- Snapshot guarda `metrics_json` do workspace.
- UI do Command Center permite criar workspace, comparar e gerar snapshot.
- Testes automatizados cobrem criacao, comparacao e snapshot.
