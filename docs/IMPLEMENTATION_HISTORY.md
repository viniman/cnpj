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

1. Criar branch `feature/<numero>-<slug>`.
2. Registrar docs ou decisao antes de implementar feature grande.
3. Fazer commits pequenos por unidade logica.
4. Rodar testes antes de encerrar a etapa.
5. Atualizar este historico com o que mudou e como verificar.

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
