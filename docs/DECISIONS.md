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

## ADR-008 - ICP estruturado limita o agente SDR

Data: 2026-07-20

Decisao:

- O ICP do agente SDR deve ser uma regra estruturada em `icp_rules`.
- A fila SDR deve ser criada apenas por uma funcao de backend que aplica esses
  filtros antes de calcular prioridade.
- O agente pode sugerir ordem e motivo dentro do conjunto elegivel, mas nao
  pode incluir leads fora do ICP configurado.

Racional:

- O prompt do agente exige que ICP nao seja decidido pelo modelo.
- Sem trilho duro de ICP, uma automacao de outbound poderia mirar segmentos
  amplos demais e danificar reputacao/compliance.
- Regra estruturada permite auditoria, reuso em playbooks e futura governanca
  multi-empresa.

Consequencias:

- `lead_priority_queue` guarda as sugestoes e explicacoes da priorizacao.
- Toda execucao de priorizacao registra `agent_actions`.
- Envio real futuro deve aceitar apenas leads que passaram por ICP, higiene,
  supressao e throttle no backend.

## ADR-009 - Respostas recebidas sao dado nao confiavel

Data: 2026-07-20

Decisao:

- Conteudo de resposta recebida deve ser tratado apenas como dado externo.
- O sistema classifica a intencao em categorias fixas e executa somente acoes
  predefinidas no backend.
- Opt-out sempre aciona supressao imediata, independentemente de aprovacao
  humana.
- Casos quentes, ambiguos, duvidas e pessoa errada viram handoff humano.

Racional:

- O prompt do agente alerta para risco de injecao por resposta recebida.
- Compliance de opt-out nao pode depender de revisao manual.
- Handoff preserva julgamento humano onde a classificacao pode afetar receita
  ou reputacao.

Consequencias:

- `reply_classifications` guarda conteudo, categoria, confianca e motivos.
- `handoffs` vira fila operacional de revisao humana.
- Cadencias ativas sao paradas quando uma resposta relevante chega.

## ADR-010 - Reunioes exigem decisao humana explicita

Data: 2026-07-20

Decisao:

- Uma resposta de interesse nao cria reuniao automaticamente.
- O sistema cria primeiro um handoff humano; a reuniao so nasce quando o
  operador registra agenda, link ou nota operacional.
- No MVP local, a reuniao e registro interno e auditavel, sem convite real de
  calendario nem envio automatico.

Racional:

- Agendamento mexe com expectativa comercial e disponibilidade humana.
- O produto ainda nao tem integracao real com calendario nem canal de resposta.
- Manter a decisao humana evita que conteudo externo ou classificacao incerta
  vire compromisso operacional sem revisao.

Consequencias:

- `meetings` se liga a `leads`, `reply_classifications` e `handoffs`.
- Criar reuniao a partir de handoff resolve a tarefa e atualiza o funil.
- Opt-out e supressao continuam bloqueando qualquer acao comercial ativa.

## ADR-011 - Command Center agrega, nao substitui fontes de verdade

Data: 2026-07-20

Decisao:

- O Command Center deve ler dados de `approval_queue`, `handoffs`,
  `meetings`, `lead_journey`, `leads` e `agent_actions`.
- Ele nao cria tabelas paralelas para pendencias ou atividades nesta fase.
- Todo item agregado preserva `source_type`, `source_id` e `origin_label`.

Racional:

- A camada de governanca precisa dar transparencia sem criar divergencia de
  estado.
- As acoes ja possuem endpoints e regras proprias em seus modulos de origem.
- Preservar origem prepara auditoria futura e multi-tenancy sem reescrever a
  semantica dos dados.

Consequencias:

- `GET /api/command-center` e uma composicao de leitura.
- A UI mostra as acoes, mas decisoes especificas continuam nas telas/rotas de
  origem ate a fase de caixa de entrada acionavel completa.
- Qualquer evolucao futura deve manter rastreabilidade ate o dado bruto.

## ADR-012 - Acoes do Command Center sao roteadas para servicos de origem

Data: 2026-07-20

Decisao:

- A inbox acionavel usa um endpoint agregador:
  `POST /api/command-center/actions`.
- O endpoint valida tipo e decisao, mas delega a execucao para os servicos de
  origem: aprovacao, handoff ou reuniao.
- O retorno sempre inclui um snapshot atualizado de `command_center`.

Racional:

- A caixa unica precisa reduzir navegacao, mas nao pode duplicar regra de
  negocio.
- Guardrails de supressao, aprovacao, handoff e agenda ja vivem nos modulos
  originais.
- Retornar snapshot atualizado simplifica a UI e evita estado visual antigo
  apos uma decisao.

Consequencias:

- Acoes na aba `Comando` continuam auditadas pelos servicos originais.
- Novos tipos de inbox devem adicionar roteamento explicito, nunca decisao por
  texto livre.
- Criacao de reuniao por handoff segue na aba `Respostas` por enquanto, porque
  exige dados de agenda.

## ADR-013 - Replay de lead e uma composicao auditavel de leitura

Data: 2026-07-20

Decisao:

- A timeline/replay por lead deve ser montada por leitura das tabelas de
  origem existentes.
- Nenhuma tabela paralela de timeline sera criada nesta fase.
- Cada item do replay preserva `source_table`, `source_id`, `kind`,
  `origin_label`, `occurred_at` e metadados suficientes para auditoria.

Racional:

- O Command Center precisa explicar o que aconteceu sem virar uma segunda fonte
  de verdade.
- As tabelas atuais ja contem eventos de jornada, aprovacao, envio, resposta,
  handoff, reuniao, conversao e acao do agente.
- Preservar ponte para a origem permite investigar qualquer decisao meses
  depois, atendendo ao requisito de transparencia radical.

Consequencias:

- A UI pode exibir replay por lead sem alterar regras operacionais.
- Evolucoes futuras podem adicionar filtros/exportacao mantendo o contrato.
- Se uma tabela de origem mudar, a composicao da timeline deve ser atualizada
  junto com testes de cobertura.
