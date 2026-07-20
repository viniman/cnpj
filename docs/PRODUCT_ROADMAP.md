# Roadmap Integrado do Produto

Este roadmap consolida os prompts mestres anexados e transforma o escopo em
fases implementaveis. O objetivo final e sair do buscador CNPJ local e chegar
em uma plataforma B2B com dados oficiais, enriquecimento, scoring, campanhas
responsaveis, agente SDR e command center multi-empresa.

## Camada 0 - Fundacao atual

Status: iniciado.

Entregue no baseline:

- MVP local em SQLite.
- Fonte oficial CNPJ automatizada.
- Consulta BrasilAPI.
- Listas, exportacao, auditoria e higiene basica.

Proximos hardenings:

- Migrar para Postgres quando a carga real crescer.
- Separar API e worker de importacao.
- Criar autenticacao real e RBAC.
- Documentar API em OpenAPI.

## Camada 1 - Growth e scoring de e-mail

Prioridade imediata.

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

## Camada 2 - Enriquecimento responsavel

Meta:

- Descobrir site oficial da empresa.
- Raspar apenas fontes publicas e permitidas.
- Respeitar `robots.txt`, cache e TTL.
- Identificar stack tecnologica e maturidade digital.

Fases:

1. Modelo `company_enrichment`, `scraping_jobs`, `scraping_cache`.
2. Fetch HTML simples com robots/rate limit.
3. Extracao de e-mails, telefones, links sociais e tecnologias.
4. Score de maturidade digital.

## Camada 3 - CRM de experimento e envio responsavel

Meta:

- Construir mini-CRM de experimento comercial, nao disparador em massa.
- Priorizar clique, resposta, cadastro e demanda criada sobre abertura.
- Preparar arquitetura futura Vercel + AWS SES + SNS + QStash.

Fases:

1. Modelo local de `leads`, `campaigns`, `campaign_variants`, `sends`,
   `events`, `conversions`, `throttle_config`, `pause_events`.
2. Simulador local de campanhas sem envio real.
3. Trilho duro de supressao antes de qualquer envio.
4. Documentacao de DNS SPF/DKIM/DMARC e SES.
5. Integracao SES apenas apos ambiente e dominio validados.

## Camada 4 - Agente SDR semi-supervisionado

Meta:

- Agente escolhe, sugere e acompanha, mas os trilhos duros ficam em codigo.
- Comecar com aprovacao humana antes de envio autonomo.

Fases:

1. `icp_rules`, `sequences`, `sequence_steps`, `lead_journey`.
2. Priorizacao de leads elegiveis sem envio automatico.
3. Log `agent_actions` com motivo, ferramenta e resultado.
4. Classificacao de respostas e handoff humano.
5. Autonomia gradual somente apos testes e confianca.

## Camada 5 - Command Center multi-empresa

Meta:

- Transformar a plataforma em produto multi-workspace com transparencia total.

Fases:

1. Perfil de empresa/workspace completo.
2. Wizard de onboarding com playbook inicial.
3. Feed de atividade e explicacao "por que".
4. Kanban CRM e caixa unica de aprovacoes.
5. OKRs/KPIs ligados a metricas reais.
6. Governanca de agente, versionamento e custo de IA.

## Camada 6 - SaaS monetizavel

Meta:

- API publica, chaves de API, creditos, planos e paridade parcial com Snov.io.

Fases:

1. `api_keys`, `credit_wallets`, `credit_transactions`.
2. Rate limit e consumo de credito no backend.
3. API REST documentada.
4. Planos e modelo comercial validavel.

## Regra de seguranca do produto

Nenhuma camada futura pode enfraquecer:

- Supressao e opt-out.
- Registro de origem do dado.
- Auditoria de exportacao/envio.
- Separacao entre dado oficial, enriquecimento e inferencia de IA.
- Revisao humana para casos ambiguos ou de alto risco.

