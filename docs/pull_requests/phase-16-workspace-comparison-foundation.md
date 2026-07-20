# PR local - Fase 16: Workspace comparison foundation

Branch: `feature/16-workspace-comparison-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de comparacao executiva multi-workspace, permitindo cadastrar
workspaces internos, comparar metricas essenciais por `org_id` e gerar snapshots
manuais.

## Implementado

- Especificacao da fase em `docs/WORKSPACE_COMPARISON_SPEC.md`.
- ADR-018 definindo comparacao como camada executiva antes do multi-tenant
  operacional completo.
- Modelo de dados:
  - `workspace_metric_snapshots`
- API:
  - `GET /api/workspaces/comparison`
  - `POST /api/workspaces`
  - `POST /api/workspaces/{id}/snapshot`
- Criacao de workspace em `organizations` + `company_profiles`.
- Calculo comparavel de empresas em listas, leads, respostas, handoffs,
  reunioes, notificacoes, custo de IA e playbook ativo.
- Painel `Comparacao executiva` no Command Center.
- Testes cobrindo criacao, comparacao e snapshot.

## Checklist de aceite

- [x] Criar workspace gera `organizations` e `company_profiles`.
- [x] Comparacao retorna todos os workspaces com metricas calculadas.
- [x] Workspace sem dados aparece com zeros.
- [x] Snapshot guarda `metrics_json` do workspace.
- [x] UI do Command Center permite criar workspace, comparar e gerar snapshot.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 60 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
workspaces_before=1
created_workspace_id=2
created_workspace_name=Smoke Workspace 20260720021357
created_vertical=servicos locais
created_companies=0
snapshot_id=1
snapshot_workspace=Smoke Workspace 20260720021357
snapshots_after=1
workspaces_after=2
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Esta fase nao troca o contexto operacional do app inteiro.
- Empresas sao contadas por listas do workspace porque a tabela bruta
  `companies` ainda e global no MVP local.
