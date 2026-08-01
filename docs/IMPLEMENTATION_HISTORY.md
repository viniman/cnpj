# Historico de Implementacao

Este arquivo registra as etapas realizadas no projeto para preservar contexto,
decisoes e criterios de verificacao.

## 2026-07-19 - Baseline do MVP local

Commit: `0d421d3 chore: establish local MVP baseline`

Estado registrado:

- Aplicacao local `Radar CNPJ Interno` em Python standard library + SQLite.
- Frontend estatico operacional em `static/`.
- Descoberta automatica da fonte oficial Receita/SERPRO via WebDAV.
- Consulta individual via BrasilAPI.
- Importacao de amostra CSV e parser limitado de ZIPs oficiais.
- Busca/filtros de empresas, detalhe com socios, listas, higiene de e-mail,
  supressao, exportacao CSV/XLSX e auditoria.
- Testes unitarios basicos passando.

Motivo do baseline:

- O diretorio ainda nao era um repositorio Git.
- A partir deste ponto, toda etapa relevante deve ter branch e commits
  atomicos seguindo Conventional Commits.

## Protocolo de trabalho

O fluxo de issues, branches, commits e PRs segue `docs/DEVELOPMENT_GUIDELINES.md`.
Em resumo, cada fase relevante deve ter branch semantica, commits atomicos com
Conventional Commits, PR documentado e verificacao registrada. Nomes de branch,
commits e PRs nao devem expor ferramenta interna, agente de IA ou coautoria
automatica.

## 2026-08-01 - Fase 42: Decisões de arquitetura e próximas fases

Issue: https://github.com/viniman/cnpj/issues/3

Branch: `docs/architecture-next-phases`

Objetivo:

- Consolidar as decisões tomadas após a fase 41 antes de tocar no código de
  migração Postgres, NestJS, Next.js ou refatoração de cadências.

Implementado:

- Livro razão `docs/NEXT_ARCHITECTURE_LEDGER.md` com arquitetura alvo,
  Postgres central, schemas separados, Python ETL, NestJS/Prisma, Next.js,
  histórico mensal, BrasilAPI complementar, API AI-first e 18 diferenciais
  futuros.
- Índice `docs/PHASE_HISTORY_INDEX.md` apontando para os documentos locais das
  fases 01 a 42, já que as fases antigas não tiveram PR remoto individual no
  GitHub.
- Guia `docs/DEVELOPMENT_GUIDELINES.md` para issues, branches, commits e PRs
  sem marca de ferramenta, IA ou coautoria automática.
- Guia `docs/UI_INTERFACE_PRINCIPLES.md` para produto cliente e super admin.
- ADRs 044 a 047 em `docs/DECISIONS.md`.
- Atualização de `docs/ARCHITECTURE.md`, `docs/PRODUCT_ROADMAP.md` e `README.md`
  apontando o novo norte.

Como verificar:

```powershell
git diff --stat
```

Observações:

- Não havia PRs abertas no GitHub no início da fase.
- Esta fase altera apenas documentação.
- Branches antigas de fase podem ser removidas após verificação de que estão
  contidas em `main`.

## 2026-08-01 - Fase 43: Migrations SQL do staging Postgres

Issue: https://github.com/viniman/cnpj/issues/7

Branch: `feature/43-postgres-staging-migrations`

Objetivo:

- Separar bootstrap Docker de migrations reais do `receita_staging` e iniciar
  o histórico versionado de schema bruto da Receita.

Implementado:

- Migration `infra/postgres/migrations/20260801190000_create_receita_staging_raw_tables.sql`
  com tabelas e índices brutos da Receita.
- Convenção `YYYYMMDDHHMMSS_descriptive_slug.sql` para migrations SQL de
  staging.
- Documento `docs/POSTGRES_MIGRATION_CONVENTIONS.md` explicando bootstrap,
  staging SQL e Prisma.
- Script `scripts/write_postgres_staging_sql.ps1` lendo migrations em ordem.
- Testes focados para padrão de migrations e separação do bootstrap.

Como verificar:

```powershell
python -m unittest tests.test_postgres_migrations tests.test_local_postgres_foundation tests.test_postgres_staging
```

## 2026-07-19 - Roadmap integrado e scoring avancado de e-mail

Branch: `feature/01-product-roadmap-and-email-scoring`

Commits:

- `709e14d docs: define roadmap and email scoring plan`
- `b0ac29d feat: add advanced email scoring`

Implementado:

- Roadmap das novas camadas: growth/scoring, enriquecimento, envio
  responsavel, agente SDR, command center e SaaS.
- ADRs iniciais sobre MVP local, prioridade do scoring antes de envio e
  restricoes para envio real.
- Especificacao do scoring avancado de e-mail.
- Modulo `radar_cnpj/email_scoring.py` com algoritmo puro e versionado.
- Tabelas `email_classifications`, `known_shared_domains` e `email_score_log`.
- Servico para pontuar e-mails avulsos, por empresa ou por lista.
- Endpoint `POST /api/emails/score`.
- UI de Higiene com botao `Pontuar emails`.
- Testes cobrindo decisor, descartavel, match com socio e contato
  compartilhado entre CNPJs.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 11 tests
OK
```

## 2026-07-20 - Inicio da fase 02 de enriquecimento empresarial

Branch: `feature/02-company-enrichment-foundation`

Estado inicial:

- Fase 01 mesclada localmente no `master` por fast-forward.
- Nao ha remoto Git configurado; PRs sao registrados em `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 11 tests`, `OK`.

Meta da fase:

- Criar a fundacao de enriquecimento responsavel por HTML/URL explicita.
- Persistir sinais em tabela propria, sem sobrescrever dados oficiais.
- Respeitar `robots.txt`, cache e TTL.
- Expor API local e testes automatizados.

Documento principal:

- `docs/COMPANY_ENRICHMENT_SPEC.md`

Commits:

- `898775a docs: define company enrichment phase`
- `2f60285 feat: add company enrichment foundation`

Implementado:

- Tabelas `company_enrichment`, `scraping_jobs` e `scraping_cache`.
- Modulo `radar_cnpj/company_enrichment.py` para extrair e-mails, telefones,
  redes sociais, tecnologias e score de maturidade digital.
- Respeito a `robots.txt` antes de coleta externa por URL.
- Cache de HTML por URL com TTL configuravel.
- Servicos `enrich_company` e `get_company_enrichment`.
- Endpoints `POST /api/enrichment/company` e
  `GET /api/enrichment/company/{company_id}`.
- Aba `Enriquecimento` na UI local e botao `Enriquecer` no detalhe da empresa.
- Testes de parser, technology checker, score, cache e persistencia.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 16 tests
OK
```

## 2026-07-20 - Inicio da fase 03 de CRM de experimento

Branch: `feature/03-email-experiment-foundation`

Estado inicial:

- Fase 02 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 16 tests`, `OK`.

Meta da fase:

- Criar leads a partir de listas qualificadas.
- Criar campanhas e variantes em modo simulado.
- Planejar envios simulados com trilhos duros de higiene, score e supressao.
- Registrar eventos e funil sem chamar provedor externo.

Documento principal:

- `docs/EMAIL_EXPERIMENT_SPEC.md`

Commits:

- `87801e3 docs: define email experiment phase`
- `2a3ccce feat: add simulated email experiment backend`
- `af8097c feat: add email experiment workspace UI`
- `656eb0c fix: commit API writes before responding`

Implementado:

- Tabelas `leads`, `campaigns`, `campaign_variants`, `sends`, `events`,
  `conversions`, `throttle_config` e `pause_events`.
- Modulo `radar_cnpj/email_experiments.py` com UTM, funil e regras de
  elegibilidade.
- Criacao de leads a partir de listas, com bloqueio por higiene, score e
  supressao.
- Criacao de campanhas sempre em `mode = simulated`.
- Simulacao de envios com provider `simulated`.
- Registro manual de eventos de funil, incluindo bounce/complaint com
  supressao automatica.
- Endpoints `/api/experiments/*`.
- Aba `Experimentos` no frontend local.
- Testes cobrindo guardrails, simulacao e supressao por bounce.
- Correcao do servidor para commitar escritas antes de responder HTTP,
  evitando leitura desatualizada em chamadas encadeadas rapidas.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 19 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=true
companies_added=3
leads_total=3
leads_eligible=1
leads_blocked=2
campaign_mode=simulated
simulated_sent=1
simulated_blocked=2
```

## 2026-07-20 - Inicio da fase 04 de templates versionados

Branch: `feature/04-email-template-foundation`

Estado inicial:

- Fase 03 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 19 tests`, `OK`.

Meta da fase:

- Criar templates reutilizaveis com assunto/corpo editaveis.
- Versionar cada alteracao sem sobrescrever historico.
- Renderizar variaveis com dados reais de empresa.
- Injetar rodape de compliance no backend.

Documento principal:

- `docs/EMAIL_TEMPLATE_SPEC.md`

Commits:

- `2e14f5e docs: define email template phase`
- `8f79680 feat: add versioned email template backend`
- `b273b4d feat: add email template workspace UI`

Implementado:

- Tabelas `email_templates` e `email_template_versions`.
- Modulo `radar_cnpj/email_templates.py` com extracao de variaveis,
  validacao de variaveis de sistema, contexto de empresa e renderizacao.
- Criacao de template com versao 1 ativa.
- Criacao de nova versao sem sobrescrever historico.
- Preview com dados reais de empresa.
- Rodape de compliance injetado pelo backend.
- Endpoints `/api/templates/*`.
- Aba `Templates` no frontend local.
- Botao para aplicar template renderizado no formulario de campanha simulada.
- Testes cobrindo criacao, versionamento, renderizacao e bloqueio de variaveis
  de compliance editaveis.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 24 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=true
template_id=1
initial_version=1
active_version=2
versions=2
footer_injected=true
body_has_cta=true
```

## 2026-07-20 - Inicio da fase 05 de sequencias semi-supervisionadas

Branch: `feature/05-sequence-supervision-foundation`

Estado inicial:

- Fase 04 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 24 tests`, `OK`.

Meta da fase:

- Criar sequencias com passos baseados em templates versionados.
- Inscrever leads de listas em jornadas.
- Criar fila de aprovacao humana por passo.
- Executar apenas passo aprovado, em modo simulado.
- Registrar decisoes e execucoes em `agent_actions`.

Documento principal:

- `docs/SEQUENCE_SUPERVISION_SPEC.md`

Commits:

- `66e5d30 docs: define sequence supervision phase`
- `7019dc5 feat: add semi supervised sequence backend`
- `b371c61 feat: add sequence supervision workspace UI`
- `fffe766 docs: add phase 05 sequence supervision notes`
- `a3ca242 fix: route sequence journeys before sequence detail`

Implementado:

- Tabelas `sequences`, `sequence_steps`, `lead_journey`, `approval_queue` e
  `agent_actions`.
- Criacao de sequencias com passos baseados em templates versionados.
- Inscricao de listas em jornadas apenas para leads elegiveis.
- Criacao automatica de aprovacao humana para cada passo preparado.
- Aprovacao cria envio simulado e evento `sent`; rejeicao nao cria envio.
- Jornada avanca para espera do proximo passo ou finaliza quando nao ha mais
  passos.
- Preparacao manual do proximo passo para manter a fase semi-supervisionada.
- Log de decisoes e execucoes em `agent_actions`.
- Endpoints `/api/sequences/*`, `/api/approvals/*` e `/api/agent-actions`.
- Aba `Sequencias` na UI local com construtor de cadencia, fila de aprovacao,
  jornadas e logs.
- Testes cobrindo inscricao elegivel, aprovacao, proximo passo e rejeicao.
- Teste HTTP de regressao garantindo que `/api/sequences/journeys` nao seja
  interpretado como `/api/sequences/{id}`.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 28 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
company_id=7
company_email=comercial@prismafin.com.br
list_id=7
companies_added=1
template_ids=4,5
sequence_id=2
enrolled=1
approvals_created=1
approval_id=2
approval_status=approved
send_id=8
journey_status_after_approval=waiting
prepared_next=True
agent_actions_total=5
```

## 2026-07-20 - Inicio da fase 06 de ICP e priorizacao SDR

Branch: `feature/06-icp-prioritization-foundation`

Estado inicial:

- Fase 05 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 28 tests`, `OK`.

Meta da fase:

- Criar regras ICP estruturadas em banco.
- Priorizar empresas/leads elegiveis a partir de lista ou base.
- Bloquear suprimidos, e-mails fracos e contatos fora do ICP no backend.
- Registrar decisoes e motivos em `agent_actions`.
- Expor API e UI local para fila SDR.

Documento principal:

- `docs/ICP_PRIORITIZATION_SPEC.md`

Commits:

- `99bcfcc docs: define icp prioritization phase`
- `dcf0f0a feat: add icp prioritization backend`
- `6d7eff8 feat: add icp prioritization workspace UI`
- `3ebdcaf docs: add phase 06 icp prioritization notes`

Implementado:

- Tabelas `icp_rules` e `lead_priority_queue`.
- Criacao/listagem de ICP com criterios estruturados.
- Priorizacao a partir de lista ou base inteira.
- Reuso dos guardrails de higiene, score de e-mail e supressao.
- Bloqueio por UF, cidade, CNAE, setor, porte, score da empresa e score do
  e-mail.
- Calculo de `fit_score` e `priority_score` com explicacao auditavel.
- Aceite/rejeicao humana de sugestoes da fila SDR.
- Registro de priorizacao e decisoes em `agent_actions`.
- Endpoints `/api/icp-rules/*` e `/api/priority-queue/*`.
- Aba `ICP SDR` no frontend local.
- Testes cobrindo match de ICP, bloqueio de suprimidos e decisao humana.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 30 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
company_id=7
company_email=comercial@prismafin.com.br
list_id=9
companies_added=1
icp_rule_id=2
suggested=1
updated=0
blocked=0
queue_item_id=1
priority_score=69
accepted_status=accepted
agent_actions_total=8
```

## 2026-07-20 - Inicio da fase 07 de respostas e handoff

Branch: `feature/07-reply-handoff-foundation`

Estado inicial:

- Fase 06 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 30 tests`, `OK`.

Meta da fase:

- Classificar respostas recebidas em categorias fixas.
- Aplicar opt-out como supressao imediata.
- Parar cadencias quando houver resposta relevante.
- Criar handoffs humanos para interesse, duvida, ambiguidade e casos sensiveis.
- Registrar classificacoes e decisoes em `agent_actions`.

Documento principal:

- `docs/REPLY_HANDOFF_SPEC.md`

Commits:

- `6f99969 docs: define reply handoff phase`
- `4b5c861 feat: add reply classification handoff backend`
- `4716986 feat: add reply handoff workspace UI`
- `4c5f673 docs: add phase 07 reply handoff notes`
- `57720b7 docs: record phase 07 smoke verification`

Implementado:

- Tabelas `reply_classifications` e `handoffs`.
- Classificador deterministico inicial para categorias fixas.
- Opt-out por resposta grava `opt_outs` e `suppression_list`.
- Atualizacao de status de lead conforme classificacao.
- Parada de jornadas ativas quando resposta relevante chega.
- Handoff humano para interesse, duvida, pessoa errada, ambiguidade,
  autoresposta e opt-out.
- Resolucao/dispensa de handoffs com nota.
- Registro de classificacao, handoff e decisoes em `agent_actions`.
- Endpoints `/api/replies/*` e `/api/handoffs/*`.
- Aba `Respostas` no frontend local.
- Testes cobrindo opt-out, interesse, ambiguidade, recusa e resolucao.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 34 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
company_id=7
company_email=comercial@prismafin.com.br
list_id=10
companies_added=1
leads_eligible=1
reply_id=1
classification=interest_meeting
handoff_id=1
handoff_priority=high
handoff_status_after_resolve=resolved
agent_actions_total=11
```

## 2026-07-20 - Inicio da fase 08 de reunioes e agenda

Branch: `feature/08-meeting-scheduling-foundation`

Estado inicial:

- Fase 07 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 34 tests`, `OK`.

Meta da fase:

- Criar registros de reuniao ligados a leads, respostas e handoffs.
- Permitir que humano transforme handoff em proxima acao comercial concreta.
- Bloquear reunioes para opt-out ou e-mail suprimido.
- Atualizar status do lead e funil quando reuniao e criada ou concluida.
- Expor API e UI local para agenda operacional.

Documento principal:

- `docs/MEETING_SCHEDULING_SPEC.md`

Commits:

- `81a98f0 docs: define meeting scheduling phase`
- `433a916 feat: add meeting scheduling backend`
- `ca7a53a feat: add meeting scheduling workspace UI`
- `0607319 docs: add phase 08 meeting scheduling notes`

Implementado:

- Tabela `meetings`.
- Criacao de reuniao por `lead_id` ou por `handoff_id`.
- Bloqueio de reuniao para lead em opt-out ou e-mail suprimido.
- Resolucao automatica do handoff quando humano cria reuniao por handoff.
- Atualizacao de lead para `meeting_scheduled`, `qualified` ou
  `meeting_review` conforme status.
- Conversoes `meeting_scheduled` e `meeting_completed`.
- Registros em `agent_actions` para criacao, resolucao de handoff e status.
- Endpoints `/api/meetings/*` e `/api/handoffs/{id}/meeting`.
- Controles de reuniao na aba `Respostas`.
- Testes cobrindo criacao por handoff, bloqueio por opt-out e conclusao.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 37 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
company_id=11
company_email=dados@axisanalytics.com.br
list_id=12
companies_added=1
leads_eligible=1
lead_id=20
reply_id=3
classification=interest_meeting
handoff_id=3
handoff_priority=high
meeting_id=1
meeting_status_after_create=scheduled
meeting_status_after_update=completed
meetings_listed=1
agent_actions_total=18
```

## 2026-07-20 - Inicio da fase 09 de Command Center

Branch: `feature/09-command-center-foundation`

Estado inicial:

- Fase 08 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 37 tests`, `OK`.

Meta da fase:

- Criar uma API agregadora de Command Center.
- Unificar pendencias humanas de aprovacoes, handoffs e reunioes.
- Mostrar feed de atividade com origem e motivo.
- Expor Kanban CRM a partir dos estados de leads e jornadas.
- Adicionar aba `Comando` no frontend local.

Documento principal:

- `docs/COMMAND_CENTER_SPEC.md`

Commits:

- `1a7d6bf docs: define command center phase`
- `b6733bb feat: add command center aggregator API`
- `cd81d6d feat: add command center workspace UI`
- `9895c83 docs: add phase 09 command center notes`

Implementado:

- API `GET /api/command-center`.
- Metricas compactas de aprovacoes, handoffs, reunioes, leads ativos e acoes.
- Inbox unificada de `approval_queue`, `handoffs` e `meetings`.
- Kanban CRM a partir de `leads` e ultimo `lead_journey`.
- Feed de atividade a partir de `agent_actions`, com origem e motivo.
- Aba `Comando` no frontend local.
- CSS de Kanban operacional.
- Teste automatizado cobrindo inbox, Kanban e feed.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 38 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
company_email=dados@axisanalytics.com.br
list_id=13
companies_added=1
sequence_id=3
approvals_created=1
lead_id=21
handoff_id=4
meeting_id=2
metrics_pending_approvals=2
metrics_pending_handoffs=2
metrics_open_meetings=1
inbox_source_types=approval,handoff,meeting
kanban_columns=7
kanban_cards=14
activity_items=22
```

## 2026-07-20 - Inicio da fase 10 de inbox acionavel

Branch: `feature/10-command-center-action-inbox`

Estado inicial:

- Fase 09 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 38 tests`, `OK`.

Meta da fase:

- Criar endpoint unico de decisao para a inbox do Command Center.
- Permitir aprovar/rejeitar `approval_queue` pela aba `Comando`.
- Permitir resolver/dispensar `handoffs` pela aba `Comando`.
- Permitir concluir/cancelar/no-show de `meetings` pela aba `Comando`.
- Atualizar metricas, inbox, Kanban e feed apos decisao.

Documento principal:

- `docs/COMMAND_ACTION_INBOX_SPEC.md`

Commits:

- `d62b81b docs: define command center action inbox phase`
- `e58d72d feat: add command center inbox actions API`
- `c7436bd feat: add command center inbox action UI`
- `9895d04 docs: add phase 10 command action inbox notes`

Implementado:

- Endpoint `POST /api/command-center/actions`.
- Roteamento explicito para aprovar/rejeitar `approval_queue`.
- Roteamento explicito para resolver/dispensar `handoffs`.
- Roteamento explicito para concluir/cancelar/no-show de `meetings`.
- Payload de inbox com `actions` por item.
- Campo de nota e botoes de acao na aba `Comando`.
- Re-renderizacao da UI pelo snapshot atualizado do Command Center.
- Testes cobrindo as tres familias e decisao invalida.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 41 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
list_id=15
company_id=11
lead_id=23
approvals_created=1
approval_id=6
approval_status=approved
handoff_id=6
handoff_status=resolved
meeting_id=4
meeting_status=completed
snapshot_inbox_items=5
final_inbox_items=5
kanban_columns=7
activity_items=36
```

## 2026-07-20 - Inicio da fase 11 de replay por lead

Branch: `feature/11-lead-replay-timeline`

Estado inicial:

- Fase 10 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 41 tests`, `OK`.

Meta da fase:

- Criar replay/auditoria por lead a partir das tabelas de origem.
- Permitir reconstruir jornada, aprovacoes, envios, respostas, handoffs,
  reunioes, conversoes e acoes do agente em ordem cronologica.
- Expor API e UI local no Command Center.
- Preservar origem, motivo e metadados de cada item.

Documento principal:

- `docs/LEAD_REPLAY_TIMELINE_SPEC.md`

Commits:

- `033007e docs: define lead replay timeline phase`
- `24be57a feat: add lead replay timeline API`
- `c2f2e4f feat: add lead replay timeline UI`

Implementado:

- Endpoint `GET /api/leads/{lead_id}/timeline`.
- Composicao de timeline por leitura das tabelas de origem.
- Inclusao de lead, empresa, fila SDR, jornadas, aprovacoes, envios, eventos,
  respostas, handoffs, reunioes, conversoes e `agent_actions`.
- Cada item preserva `source_table`, `source_id`, `kind`, `origin_label`,
  `detail` e `metadata`.
- Ordenacao cronologica ascendente com desempate operacional estavel.
- Painel `Replay por lead` na aba `Comando`.
- Botao `Replay` nos cards do Kanban.
- Testes cobrindo timeline completa e lead inexistente.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 43 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
lead_id=25
list_id=16
sequence_id=6
approval_id=7
timeline_items=21
actions=7
approvals=2
replies=1
handoffs=2
meetings=2
conversions=2
first_kind=lead
kinds=agent_action,approval,approval_decision,conversion,event,handoff,handoff_decision,journey,lead,lead_status,meeting,meeting_status,reply,send
```

## 2026-07-20 - Inicio da fase 12 de OKRs e KPIs

Branch: `feature/12-okr-kpi-foundation`

Estado inicial:

- Fase 11 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 43 tests`, `OK`.

Meta da fase:

- Criar catalogo de KPIs com formulas explicitas.
- Criar objetivos e key results ligados a `kpi_key`.
- Calcular progresso a partir das tabelas reais do funil.
- Expor API e painel local no Command Center.

Documento principal:

- `docs/OKR_KPI_SPEC.md`

Commits:

- `6ffbff7 docs: define okr kpi phase`
- `7e373a1 feat: add okr kpi backend`
- `9ba5f58 feat: add okr kpi command panel`

Implementado:

- Tabelas `kpi_definitions`, `objectives` e `key_results`.
- Catalogo default com 7 KPIs do funil real.
- Endpoint `GET /api/okrs`.
- Endpoint `POST /api/okrs`.
- OKR default sintetico quando nao ha objetivo salvo.
- Criacao de objetivo com validacao de `kpi_key` e meta positiva.
- Progresso de KR calculado por valor atual / meta.
- Painel `OKRs e KPIs` na aba `Comando`.
- Testes cobrindo calculo de KPI, OKR default, criacao e erro de KPI
  desconhecido.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 46 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
kpis=7
default_objective_before=default
created_objective_id=1
created_kr_kpi=meetings_completed
created_kr_progress=100
meetings_completed_value=4
objectives_after=1
first_saved_objective=1
```

## 2026-07-20 - Inicio da fase 13 de governanca do agente

Branch: `feature/13-agent-governance-foundation`

Estado inicial:

- Fase 12 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 46 tests`, `OK`.

Meta da fase:

- Versionar configuracoes do agente SDR.
- Criar staging e ativacao explicita de versoes.
- Registrar simulacoes locais sem chamada real de LLM.
- Registrar custo estimado de IA por operacao/modelo/lead.
- Expor API e painel no Command Center.

Documento principal:

- `docs/AGENT_GOVERNANCE_SPEC.md`

Commits:

- `8385531 docs: define agent governance phase`
- `80e81a7 feat: add agent governance backend`
- `3513935 feat: add agent governance command panel`

Implementado:

- Tabelas `agent_config_versions`, `agent_simulations` e `agent_cost_log`.
- Configuracao default ativa do agente SDR.
- Criacao de versoes em `staging`.
- Ativacao explicita de versao, arquivando a ativa anterior.
- Simulacao local deterministica sem chamada real de LLM.
- Registro de custo estimado por operacao, modelo, lead e versao.
- Endpoint `GET /api/agent-governance`.
- Endpoints `POST /api/agent-governance/configs`,
  `POST /api/agent-governance/configs/{id}/activate`,
  `POST /api/agent-governance/simulations` e
  `POST /api/agent-governance/costs`.
- Painel `Governanca do agente` na aba `Comando`, com resumo, versoes,
  simulacoes e custos recentes.
- Testes cobrindo default, criacao, ativacao, simulacao e custo agregado.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 50 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
active_before=1
created_config_id=3
created_version=3
created_status=staging
activated_status=active
active_after=3
simulation_id=2
simulation_decision=requires_human_review
cost_id=2
total_calls=2
total_tokens=1240
estimated_cost=0.024
```

## 2026-07-20 - Inicio da fase 14 de biblioteca de playbooks

Branch: `feature/14-playbook-library-foundation`

Estado inicial:

- Fase 13 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 50 tests`, `OK`.

Meta da fase:

- Criar biblioteca de playbooks reutilizaveis por workspace.
- Versionar conteudo estruturado de ICP, copy, cadencia, OKR e governanca.
- Permitir aplicacao explicita do playbook ao workspace interno.
- Expor API e painel local no Command Center.

Documento principal:

- `docs/PLAYBOOK_LIBRARY_SPEC.md`

Commits:

- `0a92580 docs: define playbook library phase`
- `988c1f0 feat: add playbook library backend`
- `50f0a41 feat: add playbook command panel`
- `285a4d3 fix: make playbook bootstrap idempotent`

Implementado:

- Tabelas `company_profiles`, `playbooks`, `playbook_versions` e
  `workspace_playbook_applications`.
- Perfil default do workspace interno.
- Playbook default `Outbound B2B Servicos Locais`.
- Criacao de playbook com versao 1 ativa.
- Criacao de nova versao, arquivando a ativa anterior.
- Aplicacao explicita de playbook/versao ao workspace.
- Endpoint `GET /api/playbooks`.
- Endpoints `POST /api/playbooks`, `POST /api/playbooks/{id}/versions` e
  `POST /api/playbooks/{id}/apply`.
- Painel `Playbooks` na aba `Comando`, com resumo, biblioteca, versoes e
  aplicacao ao workspace.
- Bootstrap idempotente para perfil/playbook default.
- Testes cobrindo default, criacao, versionamento e aplicacao.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 54 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
defaults_before=1
created_playbook_id=2
created_active_version=1
created_version_id=3
created_version_number=2
active_application_id=1
active_playbook_name=Smoke Playbook 20260720015844
active_version=2
playbooks_after=2
```

## 2026-07-20 - Inicio da fase 15 de notificacoes proativas

Branch: `feature/15-notification-center-foundation`

Estado inicial:

- Fase 14 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 54 tests`, `OK`.

Meta da fase:

- Criar fila local de notificacoes proativas.
- Gerar alertas auditaveis para handoffs, campanhas pausadas e OKRs.
- Permitir marcar notificacao como lida ou dispensada sem alterar a origem.
- Expor API e painel local no Command Center.

Documento principal:

- `docs/NOTIFICATION_CENTER_SPEC.md`

Commits:

- `052fd05 docs: define notification center phase`
- `a556136 feat: add notification center backend`
- `a953cd5 feat: add notification command panel`

Implementado:

- Tabela `notifications`.
- Geracao local idempotente para:
  - handoffs pendentes relevantes;
  - `pause_events` ativos;
  - key results atingidos;
  - key results em risco com prazo proximo.
- Endpoint `GET /api/notifications`.
- Endpoint `POST /api/notifications/generate`.
- Endpoints `POST /api/notifications/{id}/mark-read` e
  `POST /api/notifications/{id}/dismiss`.
- Painel `Notificacoes proativas` na aba `Comando`, com resumo, lista e
  acoes.
- Testes cobrindo geracao, idempotencia e decisoes sem alterar a origem.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 57 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

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

## 2026-07-20 - Inicio da fase 16 de comparacao multi-workspace

Branch: `feature/16-workspace-comparison-foundation`

Estado inicial:

- Fase 15 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 57 tests`, `OK`.

Meta da fase:

- Criar comparacao executiva de workspaces.
- Permitir criar perfis de workspace internos.
- Calcular metricas essenciais por `org_id`.
- Criar snapshots executivos manuais.
- Expor API e painel local no Command Center.

Documento principal:

- `docs/WORKSPACE_COMPARISON_SPEC.md`

Commits:

- `691da34 docs: define workspace comparison phase`
- `34b0584 feat: add workspace comparison backend`
- `3b62647 feat: add workspace comparison panel`

Implementado:

- Tabela `workspace_metric_snapshots`.
- Criacao de workspace em `organizations` e `company_profiles`.
- Calculo executivo por workspace:
  - empresas vinculadas a listas;
  - leads ativos;
  - respostas;
  - handoffs pendentes;
  - reunioes abertas/concluidas;
  - notificacoes pendentes;
  - chamadas/tokens/custo de IA;
  - playbook ativo.
- Endpoint `GET /api/workspaces/comparison`.
- Endpoint `POST /api/workspaces`.
- Endpoint `POST /api/workspaces/{id}/snapshot`.
- Painel `Comparacao executiva` na aba `Comando`.
- Testes cobrindo criacao, comparacao por workspace e snapshot.

Como verificar:

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 60 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

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

## 2026-07-20 - Inicio da fase 17 de contexto operacional por workspace

Branch: `feature/17-workspace-context-foundation`

Estado inicial:

- Fase 16 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 60 tests`, `OK`.

Meta da fase:

- Persistir workspace ativo local.
- Expor API para ler/trocar contexto.
- Migrar dashboard, listas e notificacoes para o workspace ativo.
- Adicionar seletor de workspace na UI.

Documento principal:

- `docs/WORKSPACE_CONTEXT_SPEC.md`

Commits:

- `f2bffcf docs: define workspace context phase`
- `5122ff0 feat: add workspace context backend`
- `3c5566d feat: add workspace switcher UI`

Implementado:

- Tabela `workspace_context` com singleton local.
- Helpers de contexto ativo no backend.
- Endpoint `GET /api/workspace-context`.
- Endpoint `POST /api/workspace-context`.
- Dashboard migrado para listas/empresas do workspace ativo.
- Listas criadas, listadas, detalhadas, exportadas e editadas com escopo ativo.
- Notificacoes listadas, geradas, lidas e dispensadas com escopo ativo.
- OKRs/KPIs migrados para o workspace ativo.
- Seletor de workspace na topbar da UI.
- Recarregamento da visao aberta apos troca de workspace.
- Testes dedicados em `tests/test_workspace_context.py`.

Como verificar:

```powershell
python -m unittest tests.test_workspace_context
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 64 tests
OK
```

Smoke test HTTP apos reiniciar servidor:

```text
health=True
workspace_before=1
workspace_switch_to=2
dashboard_workspace=2
dashboard_lists=0
dashboard_companies=0
workspace_restored=1
```

## 2026-07-20 - Inicio da fase 18 de contexto em experimentos

Branch: `feature/18-experiment-context-foundation`

Estado inicial:

- Fase 17 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 64 tests`, `OK`.

Meta da fase:

- Migrar leads, campanhas, simulacoes e eventos de experimento para o workspace
  ativo.
- Bloquear acesso cruzado a campanha/lista/envio de outro workspace.
- Preservar envio real fora de escopo; o provider continua `simulated`.

Documento principal:

- `docs/EXPERIMENT_CONTEXT_SPEC.md`

Commits:

- `475281d docs: define experiment context phase`
- `7f6accf feat: scope experiments to active workspace`

Implementado:

- Supressoes e opt-outs consultados globalmente por seguranca.
- `add_suppression` auditando no workspace ativo.
- Leads de experimento criados a partir de listas do workspace ativo.
- Listagem de leads de experimento filtrada por workspace ativo.
- Campanhas criadas, listadas e detalhadas por workspace ativo.
- Simulacao recusando campanha/lista fora do workspace ativo.
- Eventos recusando envio fora do workspace ativo.
- Funil de campanha contado pelo workspace ativo.
- Aba `Experimentos` recarregando listas ao trocar workspace.
- Teste de isolamento multi-workspace em `tests/test_email_experiments.py`.

Como verificar:

```powershell
python -m unittest tests.test_email_experiments
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 65 tests
OK
```

## 2026-07-20 - Inicio da fase 19 de templates por workspace

Branch: `feature/19-template-context-foundation`

Estado inicial:

- Fase 18 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 65 tests`, `OK`.

Meta da fase:

- Migrar biblioteca de templates, versoes e renderizacao para o workspace ativo.
- Bloquear detalhe, versionamento e renderizacao de template fora do contexto.
- Preservar rodape de compliance injetado pelo backend.

Documento principal:

- `docs/TEMPLATE_CONTEXT_SPEC.md`

Commits:

- `4c573e2 docs: define template context phase`
- `b8cd137 feat: scope email templates to active workspace`

Implementado:

- Templates criados no workspace ativo.
- Listagem e detalhe de templates filtrados por workspace ativo.
- Criacao de versao bloqueada para template fora do workspace ativo.
- Renderizacao bloqueada por template ou versao fora do workspace ativo.
- Auditoria de criacao, versionamento e renderizacao no workspace ativo.
- Rodape de compliance preservado no backend.
- Teste de isolamento multi-workspace em `tests/test_email_templates.py`.

Como verificar:

```powershell
python -m unittest tests.test_email_templates
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 66 tests
OK
```

## 2026-07-20 - Inicio da fase 20 de sequencias por workspace

Branch: `feature/20-sequence-context-foundation`

Estado inicial:

- Fase 19 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 66 tests`, `OK`.

Meta da fase:

- Migrar sequencias, passos, jornadas, aprovacoes e logs de acao de cadencia
  para o workspace ativo.
- Bloquear operacoes cruzadas entre workspaces.
- Preservar aprovacao humana antes de envio simulado.

Documento principal:

- `docs/SEQUENCE_CONTEXT_SPEC.md`

Commits:

- `e2803a7 docs: define sequence context phase`
- `311ff92 feat: scope sequences to active workspace`

Implementado:

- Sequencias criadas, listadas e detalhadas no workspace ativo.
- Passos de sequencia resolvendo templates do workspace ativo.
- Inscricao validando lista/sequencia no workspace ativo.
- Jornadas e aprovacoes criadas no workspace ativo.
- Aprovar, rejeitar e preparar proximo passo bloqueiam IDs fora do contexto.
- `agent_actions` de cadencia criadas e listadas por workspace ativo.
- Campanha auxiliar de sequencia criada no workspace ativo.
- Teste de isolamento multi-workspace em `tests/test_sequences.py`.

Como verificar:

```powershell
python -m unittest tests.test_sequences
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 67 tests
OK
```

## 2026-07-20 - Inicio da fase 21 de ICP por workspace

Branch: `feature/21-icp-context-foundation`

Estado inicial:

- Fase 20 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 67 tests`, `OK`.

Meta da fase:

- Migrar regras ICP e fila de priorizacao SDR para o workspace ativo.
- Bloquear regra, lista ou sugestao de outro workspace no backend.
- Garantir que logs de priorizacao e decisao humana fiquem no contexto ativo.

Documento principal:

- `docs/ICP_CONTEXT_SPEC.md`

Commits:

- `3565f1b docs: define icp context phase`
- `8ea15fc feat: scope icp prioritization to active workspace`

Implementado:

- Regras ICP criadas, listadas e detalhadas a partir do workspace ativo.
- Priorizacao recusando regra ou lista de outro workspace.
- Candidatos de lista e leads auxiliares validados pelo workspace ativo.
- Itens de `lead_priority_queue` gravados, listados e decididos por workspace.
- Auditoria e `agent_actions` de priorizacao/decisao gravados no contexto
  ativo.
- Teste multi-workspace em `tests/test_icp_prioritization.py`.

Como verificar:

```powershell
python -m unittest tests.test_icp_prioritization
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 68 tests
OK
```

## 2026-07-20 - Inicio da fase 22 de respostas e reunioes por workspace

Branch: `feature/22-reply-meeting-context-foundation`

Estado inicial:

- Fase 21 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 68 tests`, `OK`.

Meta da fase:

- Migrar respostas, handoffs e reunioes para o workspace ativo.
- Bloquear lead, send, handoff ou meeting de outro workspace no backend.
- Preservar opt-out/supressao como trilho duro global por e-mail.

Documento principal:

- `docs/REPLY_MEETING_CONTEXT_SPEC.md`

Commits:

- `de2ef54 docs: define reply meeting context phase`
- `80a8f2b feat: scope replies and meetings to active workspace`

Implementado:

- Respostas validando lead/envio contra o workspace ativo.
- Handoffs criados, listados e decididos no workspace ativo.
- Reunioes criadas por lead ou handoff apenas no workspace ativo.
- Atualizacao de status de reuniao bloqueando item de outro workspace.
- `agent_actions`, auditoria e registros principais da fase usando o contexto
  ativo.
- Testes multi-workspace em `tests/test_reply_handoffs.py` e
  `tests/test_meetings.py`.

Como verificar:

```powershell
python -m unittest tests.test_reply_handoffs tests.test_meetings
python -m unittest tests.test_command_center
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 70 tests
OK
```

## 2026-07-20 - Inicio da fase 23 de Command Center por workspace

Branch: `feature/23-command-center-context-foundation`

Estado inicial:

- Fase 22 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 70 tests`, `OK` usando `TEMP/TMP` em `D:`
  porque o drive `C:` esta sem espaco livre no ambiente local.

Meta da fase:

- Migrar metricas, inbox, Kanban e feed do Command Center para o workspace
  ativo.
- Migrar replay por lead para o workspace ativo.
- Bloquear acoes e timelines de outro workspace por validacao nos servicos de
  origem.

Documento principal:

- `docs/COMMAND_CENTER_CONTEXT_SPEC.md`

Commits:

- `cd6fd8e docs: define command center context phase`
- `a0272be feat: scope command center to active workspace`

Implementado:

- Replay por lead filtrando pelo workspace ativo.
- Metricas, inbox, Kanban e feed de atividade do Command Center usando o
  workspace ativo.
- Inbox de reunioes e feed com joins protegidos por `org_id`.
- Acoes do Command Center permanecendo delegadas para os servicos de origem.
- Teste multi-workspace em `tests/test_command_center.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_command_center
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 71 tests
OK
```

## 2026-07-20 - Inicio da fase 24 de governanca do agente por workspace

Branch: `feature/24-agent-governance-context-foundation`

Estado inicial:

- Fase 23 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 71 tests`, `OK` usando `TEMP/TMP` em `D:`
  porque o drive `C:` esta sem espaco livre no ambiente local.

Meta da fase:

- Migrar configuracoes, simulacoes e custos do agente para o workspace ativo.
- Garantir default proprio por workspace.
- Bloquear configuracao, lead ou custo de outro workspace.

Documento principal:

- `docs/AGENT_GOVERNANCE_CONTEXT_SPEC.md`

Commits:

- `fc27dd3 docs: define agent governance context phase`
- `a246dad feat: scope agent governance to active workspace`

Implementado:

- Configuracao default do agente criada por workspace ativo.
- Listagem, ativacao e criacao de configuracoes isoladas por workspace.
- Simulacoes validando configuracao e lead no workspace ativo.
- Custos validando configuracao, lead, sequencia e acao no workspace ativo.
- Resumo de custo e listagem de custos filtrados por workspace.
- Teste multi-workspace em `tests/test_agent_governance.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_agent_governance
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 72 tests
OK
```

## 2026-07-20 - Inicio da fase 25 de playbooks por workspace

Branch: `feature/25-playbook-context-foundation`

Estado inicial:

- Fase 24 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 72 tests`, `OK` usando `TEMP/TMP` em `D:`
  porque o drive `C:` esta sem espaco livre no ambiente local.

Meta da fase:

- Migrar perfil, playbooks, versoes e aplicacao ativa para o workspace ativo.
- Garantir default idempotente por workspace.
- Bloquear playbook ou versao de outro workspace.

Documento principal:

- `docs/PLAYBOOK_CONTEXT_SPEC.md`

Commits:

- `655656b docs: define playbook context phase`
- `70aec97 feat: scope playbooks to active workspace`

Implementado:

- Perfil operacional resolvido pelo workspace ativo.
- Default de playbook criado de forma idempotente por workspace.
- Criacao, listagem e detalhe de playbooks filtrados por workspace ativo.
- Criacao de versao recusando playbook de outro workspace.
- Aplicacao de playbook/versao recusando IDs de outro workspace.
- Aplicacao ativa retornando somente o workspace ativo.
- Auditoria de playbooks gravada no contexto ativo.
- Teste multi-workspace em `tests/test_playbooks.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_playbooks
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 73 tests
OK
```

## 2026-07-20 - Inicio da fase 26 de auditoria por workspace

Branch: `feature/26-audit-context-foundation`

Estado inicial:

- Fase 25 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 73 tests`, `OK` usando `TEMP/TMP` em `D:`
  porque o drive `C:` esta sem espaco livre no ambiente local.

Meta da fase:

- Migrar leitura de auditoria operacional para o workspace ativo.
- Bloquear vazamento visual de eventos de auditoria entre empresas internas.
- Manter uma futura visao global administrativa fora do fluxo operacional.

Documento principal:

- `docs/AUDIT_CONTEXT_SPEC.md`

Commits:

- `9c69f3a docs: define audit context phase`
- `326211a feat: scope audit events to active workspace`

Implementado:

- `audit_events` migrado para `current_org_id(conn)`.
- API `/api/audit` mantendo o contrato atual, mas lendo o workspace ativo.
- Teste multi-workspace em `tests/test_workspace_context.py` provando que
  eventos de auditoria operacional nao vazam entre empresas internas.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_context
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 74 tests
OK
```

## 2026-07-20 - Inicio da fase 27 de clonagem de playbooks

Branch: `feature/27-playbook-clone-foundation`

Estado inicial:

- Fase 26 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 74 tests`, `OK` usando `TEMP/TMP` em `D:`
  porque o drive `C:` esta sem espaco livre no ambiente local.

Meta da fase:

- Permitir reuso explicito de playbook entre empresas internas.
- Criar clone independente no workspace de destino.
- Preservar auditoria e impedir compartilhamento implicito de estado.

Documento principal:

- `docs/PLAYBOOK_CLONE_SPEC.md`

Commits:

- `bd21c8b docs: define playbook clone phase`
- `a2621c5 feat: add auditable playbook cloning`

Implementado:

- Servico `clone_playbook_to_workspace`.
- Endpoint `POST /api/playbooks/{id}/clone`.
- Clone a partir da versao ativa ou de `version_id` explicito.
- Criacao de novo playbook independente no workspace de destino.
- Auditoria da clonagem no workspace de origem e de recebimento no destino.
- Bloco de clonagem na UI local de playbooks.
- Teste multi-workspace em `tests/test_playbooks.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_playbooks
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 75 tests
OK
```

## 2026-07-20 - Inicio da fase 28 de onboarding operacional

Branch: `feature/28-workspace-onboarding-wizard`

Estado inicial:

- Fase 27 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 75 tests`, `OK` usando `TEMP/TMP` em `D:`
  porque o drive `C:` esta sem espaco livre no ambiente local.

Meta da fase:

- Criar wizard local para deixar nova empresa operacional rapidamente.
- Compor workspace, perfil, playbook, ICP, template, sequencia e OKR.
- Manter auditoria e aprovacao humana sem atalhos.

Documento principal:

- `docs/WORKSPACE_ONBOARDING_SPEC.md`

Commits:

- `53aa859 docs: define workspace onboarding phase`
- `6e06d34 feat: add workspace onboarding backend`
- `fac731b feat: add onboarding wizard UI`

Implementado:

- Tabela `workspace_onboarding_runs`.
- Servico `run_workspace_onboarding`.
- Endpoint `POST /api/workspaces/onboarding`.
- Wizard cria workspace, ativa contexto e compoe playbook, ICP, template,
  sequencia, OKR e configuracao default do agente.
- Painel `Onboarding operacional` no Command Center.
- Testes dedicados em `tests/test_workspace_onboarding.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_onboarding
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 77 tests
OK
```

## 2026-07-20 - Inicio da fase 29 de execucao guiada de playbook

Branch: `feature/29-playbook-execution-plan`

Estado inicial:

- Fase 28 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 77 tests`, `OK` usando `TEMP/TMP` em `D:`
  porque o drive `C:` esta sem espaco livre no ambiente local.

Meta da fase:

- Criar plano revisavel antes de materializar um playbook.
- Aplicar plano de forma explicita e auditavel.
- Reusar servicos existentes de ICP, template, sequencia e OKR.

Documento principal:

- `docs/PLAYBOOK_EXECUTION_PLAN_SPEC.md`

Commits:

- `f136ae0 docs: define playbook execution plan phase`
- `9179569 feat: add playbook execution plans`
- `0e5bee3 feat: add playbook execution plan UI`

Implementado:

- Tabela `playbook_execution_plans`.
- Servicos `create_playbook_execution_plan`, `list_playbook_execution_plans` e
  `apply_playbook_execution_plan`.
- Endpoints para listar planos, criar plano a partir de playbook e aplicar
  plano existente.
- Plano em rascunho com `plan_json`, `diff_json`, status e artefatos criados.
- Aplicacao explicita reaproveitando os servicos existentes de playbook, ICP,
  template, sequencia e OKR.
- UI no painel de Playbooks com criacao de plano, tabela de diff/guardrails e
  acao para aplicar rascunhos.
- Testes dedicados em `tests/test_playbook_execution_plans.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_playbook_execution_plans
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 80 tests
OK
```

## 2026-07-21 - Inicio da fase 30 de credenciais e creditos SaaS

Branch: `feature/30-saas-credentials-foundation`

Estado inicial:

- Fase 29 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes pos-merge da fase 29: `Ran 80 tests`, `OK` usando `TEMP/TMP` em `D:`.

Meta da fase:

- Criar base SaaS local com chaves de API por workspace.
- Criar carteira de creditos por workspace e ledger append-only.
- Preparar trilho duro de saldo para endpoints publicos futuros.

Documento principal:

- `docs/SAAS_CREDENTIALS_SPEC.md`

Commits:

- `e55177b docs: define SaaS credentials phase`
- `1f72750 feat: add SaaS API keys and credit wallets`
- `1cc8b45 feat: add SaaS credentials command UI`

Implementado:

- Tabelas `api_keys`, `credit_wallets` e `credit_transactions`.
- Chaves de API com token completo retornado apenas uma vez.
- Persistencia apenas de hash SHA-256, prefixo e mascara.
- Revogacao auditavel de chave sem deletar historico.
- Carteira idempotente por workspace ativo.
- Ledger append-only de credito/debito com saldo negativo recusado no backend.
- Endpoint agregado `GET /api/saas/account`.
- Endpoints internos para criar/revogar chave e ajustar creditos.
- Painel `SaaS e API` no Command Center.
- Testes dedicados em `tests/test_saas_credentials.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saas_credentials
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 84 tests
OK
```

## 2026-07-21 - Inicio da fase 31 de rate limit e creditos por API

Branch: `feature/31-api-rate-credit-guardrails`

Estado inicial:

- Fase 30 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes pos-merge da fase 30: `Ran 84 tests`, `OK` usando `TEMP/TMP` em `D:`.

Meta da fase:

- Autenticar endpoint publico local por API key.
- Aplicar escopo, rate limit e saldo de creditos no backend.
- Registrar uso aceito e bloqueado em ledger de uso separado.

Documento principal:

- `docs/API_RATE_CREDIT_SPEC.md`

Commits:

- `79aa5d2 docs: define API rate credit phase`
- `d876cec feat: add API key rate limit and credit guardrails`
- `ccd4f1e feat: show API usage in SaaS command UI`

Implementado:

- Tabela `api_usage_events`.
- Excecao `ApiAccessError` com status HTTP para API publica local.
- Autenticacao por `X-API-Key` ou `Authorization: Bearer`.
- Validacao de chave ativa, escopo, saldo e rate limit antes da busca publica.
- Endpoint `GET /api/public/companies` reutilizando os filtros de empresas.
- Debito de 1 credito apenas em chamada bem-sucedida.
- Registro de chamadas aceitas e bloqueadas no agregado SaaS.
- Painel `SaaS e API` exibindo uso recente e bloqueios.
- Testes dedicados em `tests/test_api_rate_credit.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_api_rate_credit
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 90 tests
OK
```

## 2026-07-21 - Inicio da fase 32 de documentacao OpenAPI publica

Branch: `feature/32-public-openapi-docs`

Estado inicial:

- Fase 31 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Roadmap da camada SaaS aponta `API REST documentada` como proxima fase.

Meta da fase:

- Expor contrato OpenAPI local da API publica.
- Documentar autenticacao, escopo, custo, rate limit e erros da busca publica.
- Mostrar o contrato no painel interno `SaaS e API`.

Documento principal:

- `docs/PUBLIC_OPENAPI_SPEC.md`

Commits:

- `docs: define public OpenAPI phase`
- `feat: add public OpenAPI contract endpoint`
- `feat: show public API docs in SaaS panel`

Implementado:

- Funcao `public_openapi_spec` com contrato OpenAPI 3.0.3.
- Endpoint `GET /api/public/openapi.json` sem consumo de creditos.
- Documentacao de `GET /api/public/companies` com filtros, seguranca, escopo,
  custo, rate limit e erros 401/402/403/429.
- Schemas `PublicCompany`, `PublicApiUsage`, `PublicCompanySearchResult` e
  `Error`.
- Painel `SaaS e API` mostrando OpenAPI, endpoint, autenticacao, escopo, custo
  e rate limit.
- Testes dedicados em `tests/test_public_openapi.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_public_openapi
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 92 tests
OK
```

## 2026-07-21 - Inicio da fase 33 de planos SaaS

Branch: `feature/33-saas-plan-model`

Estado inicial:

- Fase 32 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Roadmap da camada SaaS aponta `Planos e modelo comercial validavel` como
  proxima fase.

Meta da fase:

- Criar catalogo local de planos SaaS.
- Criar assinatura ativa por workspace.
- Aplicar creditos incluidos via ledger append-only.
- Mostrar plano atual e catalogo no painel `SaaS e API`.

Documento principal:

- `docs/SAAS_PLAN_MODEL_SPEC.md`

Commits:

- `docs: define SaaS plan model phase`
- `feat: add SaaS plan subscriptions`
- `feat: show SaaS plan model in command UI`

Implementado:

- Tabelas `saas_plans` e `workspace_plan_subscriptions`.
- Catalogo default idempotente com planos `free`, `starter`, `growth`, `scale`
  e `internal`.
- Aplicacao de plano no workspace ativo com cancelamento da assinatura ativa
  anterior.
- Creditos incluidos no plano concedidos por `credit_transactions`.
- `credit_wallets.plan_name` sincronizado com o codigo do plano atual.
- Agregado `GET /api/saas/account` retornando planos e assinatura ativa.
- Endpoint interno `POST /api/saas/plan-subscription`.
- Painel `SaaS e API` com catalogo, assinatura e aplicacao de plano.
- Testes dedicados em `tests/test_saas_plans.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saas_plans
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 97 tests
OK
```

## 2026-07-21 - Fase 34 de segmentos salvos e ICP

Branch: `feature/34-saved-segments-icp`

Estado inicial:

- Fase 33 mesclada localmente no `master`.
- Tabela `saved_filters` ja existe no schema, mas sem servicos, endpoints ou UI.
- O prompt de growth pede que o funil de filtros possa ser salvo como segmento
  e ICP reutilizavel.

Meta da fase:

- Salvar filtros atuais da tela de empresas como segmento.
- Reaplicar segmento salvo na busca.
- Converter segmento em regra ICP estruturada.

Documento principal:

- `docs/SAVED_SEGMENT_ICP_SPEC.md`

Commits:

- `124853c docs: define saved segment ICP phase`
- `bb9ba48 feat: add saved segment services`
- `92e8960 feat: add saved segment UI`

Implementado:

- Indice `idx_saved_filters_org` para leitura por workspace.
- Servicos para normalizar filtros de empresas, criar/listar segmentos salvos
  e preservar snapshot de contagem em `filters_json._snapshot`.
- Conversao auditavel de segmento salvo para `icp_rules`, mantendo
  `criteria.source_filters`, `source_filter_id` e `source_filter_name`.
- Endpoints `GET /api/saved-filters`, `POST /api/saved-filters` e
  `POST /api/saved-filters/{id}/icp`.
- Tela `Empresas` com filtros ampliados por setor, telefone e score minimo.
- Painel `Segmentos salvos e ICP` para salvar filtros atuais, aplicar segmento
  e criar ICP a partir do segmento selecionado.
- Testes dedicados em `tests/test_saved_segments.py` cobrindo snapshot,
  reaplicacao de filtros, conversao para ICP e isolamento por workspace.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saved_segments
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 101 tests
OK
```

## 2026-07-21 - Fase 35 de scoring por workspace

Branch: `feature/35-workspace-scoring-config`

Estado inicial:

- Fase 34 mesclada localmente no `master`.
- O scoring de e-mail ja existe, mas o dicionario de prefixos ainda e fixo em
  codigo.
- O prompt de growth pede pesos editaveis por workspace, porque a importancia
  de `rh@`, `financeiro@`, `comercial@` e outros prefixos muda conforme o ICP.

Meta da fase:

- Criar configuracao ativa de scoring por workspace.
- Permitir atualizar regras de prefixo por API e UI local.
- Aplicar a configuracao em `score_email_record`.
- Manter o algoritmo puro compativel com os defaults.

Documento principal:

- `docs/WORKSPACE_SCORING_CONFIG_SPEC.md`

Commits:

- `1340010 docs: define workspace scoring config phase`
- `0832c66 feat: add workspace scoring config backend`
- `217210c feat: add scoring config UI`

Implementado:

- Tabela `workspace_scoring_configs` com uma configuracao ativa por workspace.
- Default idempotente baseado em `PREFIX_RULES`.
- Servicos para ler, normalizar e atualizar regras de prefixo e thresholds.
- Endpoints `GET /api/scoring/config` e `POST /api/scoring/config`.
- `score_email_record` aplicando regras do workspace ativo e retornando
  `scoring_config_id`, `scoring_config_name` e marcador de regra aplicada.
- Aba `Higiene` com painel `Config scoring`, editor JSON e resumo de prefixos.
- Testes dedicados em `tests/test_workspace_scoring_config.py` cobrindo default,
  customizacao de prefixo, persistencia e isolamento multi-workspace.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_scoring_config tests.test_email_scoring
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 105 tests
OK
```

## 2026-07-21 - Fase 36 de score de empresa por workspace

Branch: `feature/36-workspace-company-score-config`

Estado inicial:

- Fase 35 mesclada localmente no `master`.
- O score de e-mail ja e configuravel por workspace.
- O score de empresa ainda e global em `companies.opportunity_score`.
- O prompt de governanca exige multi-tenancy real e o prompt de growth pede
  filtros/ICPs sensiveis a setor, porte, cidade, tamanho e valor comercial.

Meta da fase:

- Criar configuracao ativa de score de empresa por workspace.
- Persistir score calculado por workspace como overlay, sem sobrescrever o
  score base cadastral.
- Aplicar o overlay em busca, detalhe e priorizacao ICP.
- Expor painel local para salvar regras JSON e recalcular lote controlado.

Documento principal:

- `docs/WORKSPACE_COMPANY_SCORE_CONFIG_SPEC.md`

Commits:

- `dcd83c4 docs: define workspace company score phase`
- `058e556 feat: add workspace company score backend`
- `440fb3f feat: add company score config UI`

Implementado:

- `score_company` agora aceita regras opcionais e preserva defaults sem banco.
- Tabelas `workspace_company_score_configs` e `company_workspace_scores`.
- Configuracao ativa idempotente por workspace.
- Recalculo controlado por workspace, com `limit` e suporte a `list_id`.
- Busca de empresas usando overlay de score do workspace via `COALESCE`.
- Detalhe de empresa exibindo motivos do overlay quando ele existe.
- Priorizacao ICP usando o score do workspace quando recalculado.
- Endpoints `GET /api/scoring/company-config`,
  `POST /api/scoring/company-config` e `POST /api/scoring/company-rescore`.
- Aba `Higiene` com painel `Score empresa`, editor JSON e recalculo local.
- Testes dedicados em `tests/test_workspace_company_score_config.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_company_score_config tests.test_scoring
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 109 tests
OK
```

## 2026-07-21 - Fase 37 de historico e rollback de score

Branch: `feature/37-scoring-config-version-history`

Estado inicial:

- Fase 36 mesclada localmente no `master`.
- Score de e-mail e score de empresa ja sao configuraveis por workspace.
- As configuracoes ainda sao atualizadas em linha, sem historico de snapshots
  nem rollback pelo produto.

Meta da fase:

- Criar historico versionado comum para score de e-mail e empresa.
- Criar versao inicial automaticamente para defaults existentes.
- Criar nova versao a cada atualizacao.
- Permitir rollback auditavel por API e UI local.

Documento principal:

- `docs/SCORING_CONFIG_VERSION_HISTORY_SPEC.md`

Commits:

- `eb0f3cf docs: define scoring config history phase`
- `60c4c8c feat: add scoring config version history`
- `7f57ed7 feat: add scoring config history UI`
- `6f8ac75 fix: make score config bootstrap idempotent`

Implementado:

- Tabela `workspace_score_config_versions` com historico comum para score de
  e-mail e de empresa.
- Versao 1 criada automaticamente para defaults existentes ou novos.
- Atualizacao de score de e-mail e empresa criando nova versao ativa.
- Rollback por snapshot antigo criando nova versao ativa.
- Endpoints `GET /api/scoring/config-versions` e
  `POST /api/scoring/config-versions/{id}/rollback`.
- Aba `Higiene` com painel `Historico scoring`, filtro por tipo e acao de
  restaurar versao.
- Bootstrap de versao inicial idempotente mesmo quando a UI carrega configs em
  paralelo.
- Testes dedicados em `tests/test_scoring_config_versions.py`.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_scoring_config_versions tests.test_workspace_scoring_config tests.test_workspace_company_score_config
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado nesta etapa:

```text
Ran 113 tests
OK
```

## 2026-07-21 - Fase 38 de diff visual de score

Branch: `feature/38-scoring-config-diff-preview`

Estado inicial:

- Fase 37 mesclada localmente no `master`.
- Configuracoes de score de e-mail e empresa ja tinham historico e rollback.
- O operador ainda precisava ler snapshots JSON manualmente para entender o
  impacto antes de restaurar uma versao antiga.

Meta da fase:

- Comparar a configuracao ativa atual com uma versao historica escolhida.
- Mostrar campos adicionados, removidos e alterados antes de rollback.
- Preservar o modelo de snapshots da fase 37 sem criar estado paralelo.

Documento principal:

- `docs/SCORING_CONFIG_DIFF_SPEC.md`

Commits:

- `1119780 docs: define scoring config diff phase`
- `06b5e57 feat: add scoring config diff endpoint`
- `1ceaed0 feat: add scoring config diff UI`

Implementado:

- Comparador deterministico de JSON para snapshots de score.
- Servico `get_score_config_version_diff`.
- Endpoint `GET /api/scoring/config-versions/{id}/diff`.
- Diff sempre no sentido `ativo atual -> versao escolhida`, que e o impacto de
  rollback.
- Isolamento por workspace ao comparar versoes.
- UI no painel `Historico scoring` com botao `Diff`, resumo e tabela de campos
  alterados.
- Confirmacao de rollback exibindo a quantidade de campos que mudarao.
- Testes cobrindo diff de e-mail, diff de empresa, isolamento por workspace e
  rota HTTP.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_scoring_config_versions tests.test_server_routes
python -m unittest discover -s tests
node --check static\app.js
```

Resultado desta etapa:

```text
python -m unittest tests.test_scoring_config_versions tests.test_server_routes
Ran 8 tests
OK

python -m unittest discover -s tests
Ran 116 tests
OK

node --check static\app.js
OK
```

## 2026-07-21 - Fase 39 de checkpoints de importacao oficial

Branch: `feature/39-official-import-checkpoints`

Estado inicial:

- Fase 38 mesclada localmente no `master`.
- A fonte oficial da Receita ja era descoberta automaticamente.
- O fluxo `mode=chunk` baixava e importava um lote limitado, mas nao guardava
  de forma estruturada onde continuar em execucoes seguintes.

Meta da fase:

- Criar checkpoints por `snapshot + chunk`.
- Permitir retomar uma importacao oficial a partir do `next_offset` salvo.
- Exibir o estado da importacao oficial na UI local.
- Manter a compatibilidade com o MVP em SQLite e preparar a fase futura de
  PostgreSQL/staging.

Documento principal:

- `docs/OFFICIAL_IMPORT_CHECKPOINT_SPEC.md`

Commits:

- `83627a1 docs: define official import checkpoint phase`
- `f5fb929 feat: add official import checkpoints`
- `3968a70 feat: add official import checkpoint UI`
- `b62751c docs: add official import checkpoint notes`

Implementado:

- Tabela `official_import_checkpoints`.
- Parser oficial com `offset` para pular estabelecimentos ativos ja
  consumidos.
- `import_official_zip_directory` retornando `offset`, `next_offset`,
  `total_rows` e `completed_chunk`.
- Checkpoint acumulando importados/erros, status, limite usado e ultimo job.
- `resume=true` em `sync_official_snapshot`.
- Endpoint `GET /api/sources/official/checkpoints`.
- Tela `Importacao` com offset manual, checkbox de retomada, tabela de
  checkpoints e acao `Retomar`.
- Testes sem rede com ZIPs oficiais minimos em diretorio temporario.

Como verificar:

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_official_sources tests.test_official_import_checkpoints
python -m unittest discover -s tests
node --check static\app.js
```

Resultado desta etapa:

```text
python -m unittest tests.test_official_sources tests.test_official_import_checkpoints
Ran 4 tests
OK

python -m unittest discover -s tests
Ran 119 tests
OK

node --check static\app.js
OK
```

## 2026-07-21 - Fase 40 de PostgreSQL staging e plano COPY

Branch: `feature/40-postgres-staging-copy-plan`

Estado inicial:

- Fase 39 mesclada localmente no `master`.
- A fonte oficial ja descobria, baixava e retomava importacoes por checkpoint.
- A carga nacional completa ainda estava documentada como evolucao futura para
  PostgreSQL/staging.

Meta da fase:

- Criar uma fundacao para carga bruta da Receita em PostgreSQL.
- Gerar DDL de staging e comandos `psql \copy` sem alterar o runtime local.
- Expor o plano na API e na tela `Importacao`.

Documento principal:

- `docs/POSTGRES_STAGING_COPY_SPEC.md`

Commits:

- `c985ffe docs: define postgres staging copy phase`
- `85ff4f4 feat: add postgres staging copy plan`
- `3ebcf8d feat: add postgres staging plan UI`

Implementado:

- Modulo `radar_cnpj.postgres_staging`.
- DDL para `receita_staging` com `unaccent`, `pg_trgm`, tabelas brutas e
  indices de busca.
- Deteccao de familias oficiais e chunks a partir dos nomes de ZIP.
- Plano COPY a partir de `source_files`, separando arquivos disponiveis,
  indisponiveis, ausentes e ignorados.
- Endpoint `GET /api/sources/official/postgres-plan`.
- Painel `Plano PostgreSQL staging` na tela `Importacao`.

Como verificar:

```powershell
python -m unittest tests.test_postgres_staging
node --check static\app.js
```

Resultado desta etapa:

```text
python -m unittest tests.test_postgres_staging
Ran 4 tests
OK

node --check static\app.js
OK
```

## 2026-08-01 - Fase 41 de PostgreSQL local como fundacao

Branch: `feature/41-local-postgres-foundation`

Estado inicial:

- Fase 40 mesclada na `main`.
- O projeto ja gerava DDL e plano COPY para staging da Receita.
- O Docker Compose ainda subia apenas a aplicacao Python.

Meta da fase:

- Adicionar PostgreSQL real ao ambiente local.
- Inicializar extensoes e schema de staging.
- Manter SQLite como runtime padrao do MVP.
- Criar scripts de verificacao e geracao de DDL.

Documento principal:

- `docs/LOCAL_POSTGRES_FOUNDATION_SPEC.md`

Commits:

- `61514b3 docs: define local postgres foundation phase`
- `421500f feat: add local postgres foundation`
- `be83e2f docs: add local postgres foundation notes`

Implementado:

- Servico `postgres` no `docker-compose.yml` com PostgreSQL 16 Alpine.
- Volume persistente `postgres-data`.
- Healthcheck `pg_isready`.
- `.env.example` com variaveis SQLite e Postgres.
- Bootstrap SQL em `infra/postgres/init/001_bootstrap.sql`.
- Script `scripts/check_postgres.ps1`.
- Script `scripts/write_postgres_staging_sql.ps1`.
- Testes em `tests/test_local_postgres_foundation.py`.

Como verificar:

```powershell
python -m unittest tests.test_local_postgres_foundation
docker compose config --services
docker compose up -d postgres
.\scripts\check_postgres.ps1
```

Resultado desta etapa:

```text
python -m unittest tests.test_local_postgres_foundation
Ran 4 tests
OK

python -m unittest discover -s tests
Ran 127 tests
OK

node --check static\app.js
OK

docker compose config --services
postgres
radar-cnpj

powershell -ExecutionPolicy Bypass -File .\scripts\write_postgres_staging_sql.ps1
DDL PostgreSQL staging escrita
```

Observacao:

- `docker compose up -d postgres` nao foi concluido nesta validacao porque o
  Docker Desktop/Linux engine nao estava ativo no ambiente local.
