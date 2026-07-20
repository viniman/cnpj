# Registro de Decisoes Arquiteturais

## ADR-001 - MVP local permanece como laboratorio, nao stack final

Data: 2026-07-19

Decisao:

- Manter o MVP atual em Python standard library + SQLite enquanto o foco for
  prototipar regras, UX e fluxo local.
- Planejar migracao futura para Next.js + TypeScript + Postgres + filas
  serverless-friendly quando a plataforma caminhar para SaaS.

Racional:

- O MVP local roda sem instalacao pesada e permite validar regras de negocio.
- A base nacional completa da Receita nao e adequada para SQLite.
- Os prompts novos assumem Vercel, AWS SES e Upstash/QStash para produto.

Consequencias:

- Features novas devem ser escritas de forma modular para serem portadas.
- Regras de negocio devem ter testes independentes de framework.

## ADR-002 - Scoring de e-mail vem antes de envio

Data: 2026-07-19

Decisao:

- Priorizar classificacao e pontuacao de e-mails antes de implementar qualquer
  envio real.

Racional:

- A qualidade da lista reduz risco de bounce, complaint e dano reputacional.
- O prompt de growth aponta esse algoritmo como diferencial real contra
  concorrentes.

Consequencias:

- O modulo de envio futuro deve consumir `email_classifications`.
- E-mails terceirizados, pessoais ou suprimidos devem ser rebaixados/bloqueados
  por regra de backend, nao por orientacao de UI.

## ADR-003 - Envio real precisa de trilhos duros e infraestrutura propria

Data: 2026-07-19

Decisao:

- Nao implementar envio real no MVP local.
- Implementar primeiro modelos, simulacao e logs; SES real so apos DNS,
  dominio dedicado, webhooks SNS e thresholds configurados.

Racional:

- Envio outbound tem risco legal e reputacional.
- SES exige configuracao de dominio, warm-up e tratamento automatico de bounce
  e complaint.

Consequencias:

- Qualquer modulo de campanha local deve nascer em modo `simulated`.
- Funcoes de envio devem sempre checar supressao no momento da acao.

## ADR-004 - Enriquecimento nao sobrescreve dado oficial

Data: 2026-07-20

Decisao:

- Dados enriquecidos por site, HTML, tecnologia ou scraping ficam em tabelas
  separadas de `companies`.
- O cadastro oficial importado da Receita continua sendo a fonte primaria para
  CNPJ, razao social, CNAE, endereco, socios e situacao.
- A UI e a API devem apresentar enriquecimento como sinal complementar, sempre
  com origem e timestamp.

Racional:

- Dados publicos de site podem mudar, estar incompletos ou pertencer a outro
  dominio semelhante.
- Misturar enriquecimento com dado oficial destruiria a rastreabilidade.
- A camada de governanca futura precisa diferenciar fato oficial, sinal
  coletado, inferencia e edicao manual.

Consequencias:

- `company_enrichment` guarda o ultimo retrato enriquecido.
- `scraping_jobs` e `scraping_cache` registram tentativa, origem e TTL.
- Descoberta automatica de dominio so deve entrar depois de validacao de
  identidade do site candidato.

## ADR-005 - Campanhas comecam em modo simulado

Data: 2026-07-20

Decisao:

- O modulo de experimento comercial nasce sem envio real.
- Campanhas, envios e eventos usam `mode = simulated` e `provider = simulated`.
- Qualquer integracao real com AWS SES depende de dominio dedicado, SPF, DKIM,
  DMARC, SNS validado, throttle e pausa automatica implementados.

Racional:

- O valor inicial esta em medir qualidade de lista, copy, segmento e funil.
- Envio real sem reputacao, unsubscribe e tratamento de bounce pode causar dano
  legal e reputacional.
- O MVP local deve exercitar regras e dados antes de tocar canal externo.

Consequencias:

- O backend pode planejar e auditar envios simulados.
- A UI deve deixar claro quando uma campanha e simulada.
- Guardrails de higiene, supressao e scoring ja sao testados nesta fase,
  preparando o caminho para SES sem confiar na interface.

## ADR-006 - Rodape de compliance e injetado pelo backend

Data: 2026-07-20

Decisao:

- Templates de e-mail guardam apenas assunto e corpo editaveis.
- O rodape de compliance, unsubscribe e privacidade e gerado no backend no
  momento da renderizacao.
- Variaveis de sistema como `{{unsubscribe_url}}` e `{{privacy_url}}` nao podem
  ser salvas no corpo editavel do template.

Racional:

- Compliance nao pode depender da disciplina de quem edita a copy.
- O agente SDR futuro tambem deve receber texto renderizado com trilhos de
  compliance ja aplicados.
- Versionar templates sem rodape editavel evita campanhas antigas com texto de
  compliance divergente.

Consequencias:

- `email_template_versions` guarda `compliance_footer` usado naquela versao.
- Renderizacao retorna `body_without_footer`, `footer` e `body`.
- Campanhas futuras devem referenciar `template_version_id` para preservar a
  copy usada no momento do experimento.

## ADR-007 - Cadencias comecam semi-supervisionadas

Data: 2026-07-20

Decisao:

- Sequencias de outbound nascem com aprovacao humana obrigatoria para cada
  passo executavel.
- O sistema pode montar o contexto e renderizar a copy, mas a execucao do passo
  depende da fila `approval_queue`.
- A execucao aprovada continua usando provider `simulated`.

Racional:

- O prompt do agente SDR recomenda nao pular a fase semi-supervisionada.
- Cadencias podem causar dano reputacional se avancarem sem revisao.
- A fila de aprovacao ja prepara o Command Center e a governanca futura.

Consequencias:

- `lead_journey` registra o estado operacional por lead/sequencia.
- `approval_queue` vira o ponto unico para decisoes humanas iniciais.
- `agent_actions` registra o que foi sugerido, aprovado, rejeitado ou
  executado, com motivo.

