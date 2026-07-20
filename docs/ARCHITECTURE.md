# Radar CNPJ Interno - Arquitetura MVP

## Decisao de stack

Este MVP foi feito para uso interno em localhost. Por isso, a primeira versao usa:

- Python standard library para API HTTP, sem dependencias externas.
- SQLite para persistencia local.
- Frontend estatico em HTML, CSS e JavaScript servido pela propria API.
- Docker opcional para ambiente reproduzivel.

Trade-off: esta stack nao e a ideal para a base nacional completa da Receita Federal. Ela e ideal para validar fluxo, filtros, listas, higiene de email, auditoria e modelo operacional com baixa friccao. A evolucao natural e migrar o banco para PostgreSQL e o importador para staging tables com COPY.

## Diagrama

```mermaid
flowchart LR
  UI["Frontend localhost"] --> API["API HTTP Python"]
  API --> DB["SQLite local"]
  API --> Import["Importador CSV / amostra Receita"]
  API --> Hygiene["Higiene de email"]
  API --> Export["Export CSV/XLSX"]
  Import --> DB
  Hygiene --> DB
  Export --> Audit["Audit logs"]
  Audit --> DB
```

## Modulos

- `radar_cnpj/database.py`: schema, conexao e bootstrap do workspace interno.
- `radar_cnpj/services.py`: casos de uso principais, busca, listas, importacao, exportacao, auditoria.
- `radar_cnpj/receita_importer.py`: parser MVP para diretorios de amostra no formato Receita.
- `radar_cnpj/official_sources.py`: descoberta WebDAV da fonte oficial, download de ZIPs e consulta BrasilAPI.
- `radar_cnpj/email_hygiene.py`: classificacao de emails, supressao e opt-out.
- `radar_cnpj/email_scoring.py`: score comercial de e-mail com explicacoes.
- `radar_cnpj/company_enrichment.py`: extracao de sinais publicos de site, technology checker e maturidade digital.
- `radar_cnpj/email_experiments.py`: regras puras de campanhas simuladas, UTM, funil e elegibilidade.
- `radar_cnpj/email_templates.py`: renderizacao de templates versionados com variaveis e rodape de compliance.
- `radar_cnpj/services.py`: tambem orquestra sequencias semi-supervisionadas,
  fila de aprovacao, ICP estruturado, fila SDR, logs do agente e Command
  Center no MVP local.
- `radar_cnpj/scoring.py`: setor, segmento, score explicavel e estimativa simples.
- `radar_cnpj/exporter.py`: geracao CSV e XLSX sem biblioteca externa.
- `static/*`: interface operacional.

## Modelo de dados

Tabelas principais:

- `organizations`, `users`: base para multi-tenant futuro.
- `companies`, `partners`, `cnaes`, `company_cnaes`: dados publicos de CNPJ.
- `lists`, `list_companies`, `tags`, `company_tags`, `saved_filters`: operacao comercial por workspace.
- `suppression_list`, `opt_outs`, `data_subject_requests`: compliance.
- `email_validations`: historico de higiene de emails.
- `email_classifications`, `email_score_log`, `known_shared_domains`: scoring avancado de e-mail.
- `company_enrichment`, `scraping_jobs`, `scraping_cache`: enriquecimento responsavel e cache.
- `leads`, `campaigns`, `campaign_variants`, `sends`, `events`,
  `conversions`, `throttle_config`, `pause_events`: CRM de experimento
  comercial em modo simulado.
- `email_templates`, `email_template_versions`: biblioteca de copy
  reutilizavel, versionada e renderizada no backend.
- `sequences`, `sequence_steps`, `lead_journey`, `approval_queue`,
  `agent_actions`: cadencias semi-supervisionadas, estado por lead, revisao
  humana e auditoria de decisoes.
- `icp_rules`, `lead_priority_queue`: regras estruturadas de cliente ideal e
  fila SDR priorizada antes de qualquer cadencia.
- `reply_classifications`, `handoffs`: classificacao de respostas recebidas e
  fila de intervencao humana.
- `meetings`: agenda operacional criada por humano a partir de lead, resposta
  ou handoff.
- `kpi_definitions`, `objectives`, `key_results`: OKRs e KPIs calculados a
  partir do funil operacional.
- `agent_config_versions`, `agent_simulations`, `agent_cost_log`: governanca
  do agente SDR, staging de configuracao, simulacoes locais e custo estimado
  de IA por operacao.
- `company_profiles`, `playbooks`, `playbook_versions`,
  `workspace_playbook_applications`: perfil operacional do workspace,
  biblioteca reutilizavel de ICP/copy/cadencia/OKR e aplicacao auditavel.
- `import_jobs`, `export_jobs`, `audit_logs`: rastreabilidade.

## Compliance por design

- Cada empresa guarda `source_name`, `source_url`, `collected_at` e `legal_basis`.
- Exportacao exige finalidade declarada.
- Exportacao gera `export_jobs` e `audit_logs`.
- Emails sao checados contra supressao e opt-out.
- Leads de campanha sao checados contra higiene, scoring e supressao antes de
  qualquer envio simulado.
- Templates recebem rodape de compliance no backend, nao por texto editavel na
  interface.
- Sequencias nao executam passos sem item aprovado em `approval_queue`.
- Aprovacoes rejeitadas nao geram registros em `sends`.
- Cada acao de sequencia registra origem e motivo em `agent_actions`.
- ICP e aplicado no backend antes de uma empresa entrar na fila SDR.
- Priorizacao bloqueia supressao, opt-out, e-mail fraco e contato
  terceirizado conforme criterio estruturado.
- Conteudo de resposta recebida e tratado como dado externo, nao instrucao.
- Opt-out por resposta grava supressao e opt-out imediatamente.
- Respostas com interesse, duvida, pessoa errada ou ambiguidade criam handoff.
- Reunioes nao sao criadas automaticamente por resposta; exigem acao humana e
  continuam bloqueadas para opt-out ou e-mail suprimido.
- Command Center preserva `source_type`, `source_id` e origem de cada item; ele
  nao substitui as regras dos modulos de origem.
- A inbox acionavel do Command Center roteia decisoes para os servicos de
  origem, mantendo guardrails e auditoria existentes.
- O replay por lead e uma composicao de leitura sobre tabelas de origem, com
  `source_table`, `source_id`, origem e metadados para auditoria.
- Key Results apontam para `kpi_key`; o valor atual vem de consulta ao funil,
  nao de snapshot salvo como verdade primaria.
- Configuracoes do agente SDR nascem em `staging` e so entram em uso por
  ativacao explicita.
- Simulacoes de agente usam regras locais deterministicas e nao fazem envio nem
  chamada real de LLM.
- Custos de IA sao registrados em tabela propria para visibilidade por modelo,
  operacao, lead e versao de configuracao.
- Playbooks sao referencias versionadas; aplicar um playbook nao sobrescreve
  dados operacionais existentes sem uma fase guiada explicita.
- Dados de socio aceitam documento mascarado, nunca CPF completo.
- A lista de supressao deve ser tratada como append-only em producao.

## Evolucao para escala

1. Migrar SQLite para PostgreSQL 16.
2. Criar tabelas de staging para EMPRECSV, ESTABELE, SOCIOCSV, CNAECSV, MUNICCSV.
3. Usar `COPY` para carga bruta e upsert em lotes.
4. Adicionar Redis + BullMQ/Celery para jobs resumiveis.
5. Usar pg_trgm/unaccent no Postgres e, se necessario, Meilisearch ou Typesense.
6. Adicionar autenticacao real, RBAC e hash de senha.
7. Adicionar backups, OpenTelemetry e testes E2E.

## Fontes automatizadas

Fonte primaria:

- Receita Federal / SERPRO public share: `https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9`
- WebDAV publico usado pela aplicacao: `https://arquivos.receitafederal.gov.br/public.php/webdav/`
- Catalogo dados.gov.br: `https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj`
- Layout oficial: `https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf`

Fonte complementar:

- BrasilAPI CNPJ: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`

O modo automatico do MVP descobre snapshots mensais, lista arquivos, baixa ZIPs pequenos de dominio e, quando solicitado, baixa um chunk oficial de Empresas/Estabelecimentos/Socios para importacao limitada. A carga nacional completa nao deve rodar em SQLite.
