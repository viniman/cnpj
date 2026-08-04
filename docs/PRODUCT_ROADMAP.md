# Roadmap Integrado do Produto

Este roadmap consolida os prompts mestres anexados e transforma o escopo em
fases implementaveis. O objetivo final e sair do buscador CNPJ local e chegar
em uma plataforma B2B com dados oficiais, enriquecimento, scoring, campanhas
responsaveis, agente SDR e command center multi-empresa.

## Camada 0 - Fundacao atual

Status: MVP local entregue e migração Postgres iniciada.

Entregue no baseline:

- MVP local em SQLite.
- Fonte oficial CNPJ automatizada.
- Consulta BrasilAPI.
- Listas, exportacao, auditoria e higiene basica.

Próximos hardenings:

- Usar Postgres local como banco de escala para staging/COPY.
- Criar migrations SQL reais timestampadas para `receita_staging`.
- Separar API e worker de importação.
- Importar snapshots oficiais em lotes retomáveis antes da migração completa.
- Calcular diffs mensais por CNPJ e manter histórico de mudanças.
- Criar autenticação real e RBAC.
- Documentar API em OpenAPI.
- Publicar `llms.txt` para API AI-first.

## Decisões pós-fase 41

O plano alvo consolidado está em `docs/NEXT_ARCHITECTURE_LEDGER.md`.

- PostgreSQL será o banco central de escala, inicialmente com schemas separados
  no mesmo database.
- Python continua como motor de ETL, download, parsing e jobs recorrentes da
  Receita.
- NestJS + Prisma será o backend de produto e dono das migrations
  operacionais.
- Next.js será a interface premium de cliente e pode assumir o super admin no
  futuro.
- SQLite será removido do fluxo principal após a migração para Postgres.
- "Sequências" migrou para "Cadências" em todo o produto (issue #64), antes
  do novo schema operacional.
- Histórico mensal, sócios antigos e alertas de mudança são diferenciais de
  produto, não apenas detalhes técnicos.
- Bootstrap Docker, migrations SQL de staging e migrations Prisma de produto
  devem permanecer separados.

## Camada 1 - Growth e scoring de e-mail

Prioridade imediata.

Status: fase 38 implementada localmente em
`feature/38-scoring-config-diff-preview`.

Meta:

- Aumentar qualidade das listas antes de qualquer modulo de disparo.
- Identificar e-mails nominais, genericos, pessoais, corporativos, suspeitos
  e provaveis terceirizados.
- Explicar cada score de forma auditavel.

Fases:

1. Dicionario PT-BR de prefixos e areas.
2. Score final de e-mail com explicacao.
3. Flag de contato compartilhado/terceirizado por repeticao em varios CNPJs.
4. Tabelas `email_classifications`, `known_shared_domains` e `email_score_log`.
5. Exposicao na UI e API.
6. Segmentos salvos a partir de filtros combinados e conversao para ICP.
7. Motor de score configuravel por workspace.
8. Score de empresa configuravel por workspace, com overlay por tenant.
9. Historico e rollback de configuracoes de score por workspace.
10. Diff visual antes de restaurar versoes de configuracao de score.

## Camada 2 - Enriquecimento responsavel

Meta:

- Descobrir site oficial da empresa.
- Raspar apenas fontes publicas e permitidas.
- Respeitar `robots.txt`, cache e TTL.
- Identificar stack tecnologica e maturidade digital.

Status: fase 02 iniciada em `feature/02-company-enrichment-foundation`.

Fases:

1. Modelo `company_enrichment`, `scraping_jobs`, `scraping_cache`.
2. Fetch HTML simples com robots/cache/TTL.
3. Extracao de e-mails, telefones, links sociais e tecnologias.
4. Score de maturidade digital.
5. Descoberta assistida de dominio oficial, com validacao antes de vincular.

## Camada 3 - CRM de experimento e envio responsavel

Meta:

- Construir mini-CRM de experimento comercial, nao disparador em massa.
- Priorizar clique, resposta, cadastro e demanda criada sobre abertura.
- Preparar arquitetura futura Vercel + AWS SES + SNS + QStash.

Status: fase 03 iniciada em `feature/03-email-experiment-foundation`.

Fases:

1. Modelo local de `leads`, `campaigns`, `campaign_variants`, `sends`,
   `events`, `conversions`, `throttle_config`, `pause_events`.
2. Simulador local de campanhas sem envio real.
3. Trilho duro de higiene, score e supressao antes de qualquer envio.
4. Templates versionados com variaveis e rodape de compliance injetado.
5. Dashboard de funil priorizando clique, resposta e conversao.
6. Documentacao de DNS SPF/DKIM/DMARC e SES.
7. Integracao SES apenas apos ambiente e dominio validados.

## Camada 4 - Agente SDR semi-supervisionado

Meta:

- Agente escolhe, sugere e acompanha, mas os trilhos duros ficam em codigo.
- Comecar com aprovacao humana antes de envio autonomo.

Status: fase 08 iniciada em `feature/08-meeting-scheduling-foundation`.

Fases:

1. Migrar nomenclatura de sequências para cadências no produto.
2. `cadences`, `cadence_steps`, jornadas de lead e `approval_queue`.
3. Inscrição de listas em cadências com aprovação humana por passo.
4. Log `agent_actions` com motivo, ferramenta e resultado.
5. `icp_rules` estruturado e priorizacao de leads elegiveis.
6. Classificacao de respostas e handoff humano.
7. Reunioes e agenda operacional a partir de handoff humano.
8. Autonomia gradual somente apos testes e confianca.

## Camada 5 - Command Center multi-empresa

Meta:

- Transformar a plataforma em produto multi-workspace com transparencia total.

Status: fase 29 implementada localmente em `feature/29-playbook-execution-plan`.

Fases:

1. Perfil de empresa/workspace completo.
2. Wizard de onboarding com playbook inicial.
3. Feed de atividade e explicacao "por que".
4. Kanban CRM e caixa unica de aprovacoes.
5. Inbox acionavel no Command Center.
6. Replay/auditoria por lead.
7. OKRs/KPIs ligados a metricas reais.
8. Governanca de agente, versionamento e custo de IA.
9. Biblioteca de playbooks reutilizaveis por workspace.
10. Notificacoes proativas para lead quente, campanha pausada e OKR em risco.
11. Comparacao multi-workspace no dashboard executivo.
12. Troca de contexto operacional por workspace.
13. Migracao gradual dos modulos restantes para `current_org_id`.
14. Experimentos comerciais simulados por workspace ativo.
15. Templates de e-mail por workspace ativo.
16. Cadencias, jornadas e aprovacoes por workspace ativo.
17. ICP e fila SDR por workspace ativo.
18. Respostas, handoffs e reunioes por workspace ativo.
19. Command Center e replay por workspace ativo.
20. Governanca do agente e custos por workspace ativo.
21. Playbooks e aplicacao ativa por workspace ativo.
22. Auditoria operacional por workspace ativo.
23. Clonagem auditavel de playbooks entre workspaces.
24. Wizard de onboarding operacional.
25. Plano de execucao guiada de playbook.

## Camada 6 - SaaS monetizavel

Meta:

- API publica, chaves de API, creditos, planos e paridade parcial com Snov.io.

Status: fase 33 implementada localmente em `feature/33-saas-plan-model`.

Fases:

1. `api_keys`, `credit_wallets`, `credit_transactions`.
2. Rate limit e consumo de credito no backend.
3. API REST documentada.
4. Planos e modelo comercial validavel.
5. `llms.txt`, exemplos e contrato publico AI-first.
6. Primeiros usos gratuitos e cobranca por creditos apos limite gratuito.

## Diferenciais de produto

A base de diferenciais futuros esta registrada em
`docs/NEXT_ARCHITECTURE_LEDGER.md`. Os principais vetores são histórico mensal,
sócios antigos, alertas de mudança, grafo societário, detecção de email de
contador, score explicável, ICP vivo, listas limpas, cadências integradas ao
dado público, CRM automático de leads quentes e API AI-first.

## Regra de seguranca do produto

Nenhuma camada futura pode enfraquecer:

- Supressao e opt-out.
- Registro de origem do dado.
- Auditoria de exportacao/envio.
- Separacao entre dado oficial, enriquecimento e inferencia de IA.
- Revisao humana para casos ambiguos ou de alto risco.

