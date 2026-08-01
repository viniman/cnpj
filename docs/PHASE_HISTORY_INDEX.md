# Índice histórico das fases

As fases 01 a 41 nasceram como branches de trabalho e foram preservadas em
documentos locais antes de haver um fluxo remoto completo de issues e PRs para
cada etapa. O histórico público do GitHub não possui um PR remoto individual
para cada uma dessas fases, mas o conteúdo foi mantido em:

- `docs/IMPLEMENTATION_HISTORY.md`;
- `docs/pull_requests/phase-*.md`;
- commits semânticos preservados no histórico Git.

Este índice existe para facilitar navegação e evitar perda de contexto.

| Fase | Tema | Documento |
| --- | --- | --- |
| 01 | Roadmap integrado e scoring avançado de e-mail | `docs/pull_requests/phase-01-product-roadmap-and-email-scoring.md` |
| 02 | Enriquecimento de empresas | `docs/pull_requests/phase-02-company-enrichment-foundation.md` |
| 03 | Experimentos de e-mail | `docs/pull_requests/phase-03-email-experiment-foundation.md` |
| 04 | Templates de e-mail | `docs/pull_requests/phase-04-email-template-foundation.md` |
| 05 | Sequências semi-supervisionadas | `docs/pull_requests/phase-05-sequence-supervision-foundation.md` |
| 06 | Priorização ICP | `docs/pull_requests/phase-06-icp-prioritization-foundation.md` |
| 07 | Respostas e handoff | `docs/pull_requests/phase-07-reply-handoff-foundation.md` |
| 08 | Agendamento de reuniões | `docs/pull_requests/phase-08-meeting-scheduling-foundation.md` |
| 09 | Command Center | `docs/pull_requests/phase-09-command-center-foundation.md` |
| 10 | Inbox acionável do Command Center | `docs/pull_requests/phase-10-command-center-action-inbox.md` |
| 11 | Replay por lead | `docs/pull_requests/phase-11-lead-replay-timeline.md` |
| 12 | OKRs e KPIs | `docs/pull_requests/phase-12-okr-kpi-foundation.md` |
| 13 | Governança do agente | `docs/pull_requests/phase-13-agent-governance-foundation.md` |
| 14 | Biblioteca de playbooks | `docs/pull_requests/phase-14-playbook-library-foundation.md` |
| 15 | Centro de notificações | `docs/pull_requests/phase-15-notification-center-foundation.md` |
| 16 | Comparação entre workspaces | `docs/pull_requests/phase-16-workspace-comparison-foundation.md` |
| 17 | Contexto de workspace | `docs/pull_requests/phase-17-workspace-context-foundation.md` |
| 18 | Experimentos por workspace | `docs/pull_requests/phase-18-experiment-context-foundation.md` |
| 19 | Templates por workspace | `docs/pull_requests/phase-19-template-context-foundation.md` |
| 20 | Sequências por workspace | `docs/pull_requests/phase-20-sequence-context-foundation.md` |
| 21 | ICP por workspace | `docs/pull_requests/phase-21-icp-context-foundation.md` |
| 22 | Respostas e reuniões por workspace | `docs/pull_requests/phase-22-reply-meeting-context-foundation.md` |
| 23 | Command Center por workspace | `docs/pull_requests/phase-23-command-center-context-foundation.md` |
| 24 | Governança do agente por workspace | `docs/pull_requests/phase-24-agent-governance-context-foundation.md` |
| 25 | Playbooks por workspace | `docs/pull_requests/phase-25-playbook-context-foundation.md` |
| 26 | Auditoria por workspace | `docs/pull_requests/phase-26-audit-context-foundation.md` |
| 27 | Clonagem de playbook | `docs/pull_requests/phase-27-playbook-clone-foundation.md` |
| 28 | Wizard de onboarding | `docs/pull_requests/phase-28-workspace-onboarding-wizard.md` |
| 29 | Plano de execução de playbook | `docs/pull_requests/phase-29-playbook-execution-plan.md` |
| 30 | Credenciais SaaS | `docs/pull_requests/phase-30-saas-credentials-foundation.md` |
| 31 | Rate limit e créditos da API | `docs/pull_requests/phase-31-api-rate-credit-guardrails.md` |
| 32 | Documentação OpenAPI pública | `docs/pull_requests/phase-32-public-openapi-docs.md` |
| 33 | Planos SaaS | `docs/pull_requests/phase-33-saas-plan-model.md` |
| 34 | Segmentos salvos e ICP | `docs/pull_requests/phase-34-saved-segments-icp.md` |
| 35 | Score de e-mail configurável | `docs/pull_requests/phase-35-workspace-scoring-config.md` |
| 36 | Score de empresa configurável | `docs/pull_requests/phase-36-workspace-company-score-config.md` |
| 37 | Histórico e rollback de score | `docs/pull_requests/phase-37-scoring-config-version-history.md` |
| 38 | Diff visual de score | `docs/pull_requests/phase-38-scoring-config-diff-preview.md` |
| 39 | Checkpoints de importação oficial | `docs/pull_requests/phase-39-official-import-checkpoints.md` |
| 40 | Plano PostgreSQL staging/COPY | `docs/pull_requests/phase-40-postgres-staging-copy-plan.md` |
| 41 | Fundação PostgreSQL local | `docs/pull_requests/phase-41-local-postgres-foundation.md` |
| 42 | Decisões de arquitetura e próximas fases | `docs/pull_requests/phase-42-architecture-next-phases.md` |
| 43 | Migrations SQL do staging Postgres | `docs/pull_requests/phase-43-postgres-staging-migrations.md` |
| 44 | Runner de migrations do staging Postgres | `docs/pull_requests/phase-44-postgres-migration-runner.md` |

## Observação sobre branches antigas

Branches antigas de fase podem ser apagadas depois de confirmado que seus
commits estão contidos em `main` e que os documentos acima preservam o contexto
de escopo, verificação e resultado.
