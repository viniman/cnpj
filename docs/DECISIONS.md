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

## ADR-014 - Key Results apontam para KPIs calculados

Data: 2026-07-20

Decisao:

- `key_results` armazenam meta, titulo e `kpi_key`.
- O valor atual do KR nao e salvo como verdade; ele e calculado por
  `kpi_definitions` no momento da leitura.
- Cada KPI declara formula textual e tabelas de origem.

Racional:

- O prompt de governanca exige KPIs rastreaveis ate dados reais.
- Salvar snapshots como verdade primaria criaria divergencia com o funil.
- Formula explicita permite ao operador entender o numero sem abrir o banco.

Consequencias:

- Mudancas de formula devem ser versionadas em fase futura.
- A UI sempre deve mostrar a formula ou origem do KPI junto do progresso.
- Criacao de KR precisa validar se o `kpi_key` existe no catalogo conhecido.

## ADR-015 - Configuracoes de agente passam por staging antes de ativar

Data: 2026-07-20

Decisao:

- Toda configuracao do agente SDR e versionada em `agent_config_versions`.
- Novas versoes nascem em `staging`.
- Somente uma versao pode estar `active` por vez.
- Custos de IA ficam em `agent_cost_log`, vinculaveis a lead, modelo,
  operacao e versao de configuracao.

Racional:

- O prompt de governanca exige rollback e explicabilidade do comportamento do
  agente.
- Mudancas de prompt/regras sem staging podem alterar decisao comercial sem
  revisao.
- Custo por acao precisa ser visivel antes de virar surpresa operacional.

Consequencias:

- A ativacao de uma versao arquiva a versao ativa anterior.
- Chamadas reais de modelo futuras devem registrar custo nessa tabela.
- Simulacoes podem ser usadas para revisar comportamento antes de ativar.

## ADR-016 - Playbooks sao referencias versionadas, nao sobrescrita automatica

Data: 2026-07-20

Decisao:

- Playbooks ficam em `playbooks` e `playbook_versions`.
- A aplicacao de um playbook ao workspace fica registrada em
  `workspace_playbook_applications`.
- Aplicar um playbook nesta fase nao sobrescreve ICP, sequencias, OKRs ou
  configuracoes do agente ja existentes.

Racional:

- O prompt de governanca exige reuso entre empresas sem automacao silenciosa.
- Playbook deve acelerar onboarding, mas toda mudanca operacional precisa ser
  explicita e auditavel.
- Versionamento permite saber qual pacote de ICP/copy/cadencia/meta foi usado
  como referencia em cada momento.

Consequencias:

- A UI mostra o playbook ativo como referencia do workspace.
- Fases futuras podem transformar uma aplicacao em preenchimento guiado de ICP,
  template, sequencia e OKR.
- Comparacao multi-workspace deve sempre indicar a versao do playbook usada.

## ADR-017 - Notificacoes sao consequencias auditaveis, nao fonte de verdade

Data: 2026-07-20

Decisao:

- Notificacoes ficam em `notifications`.
- Cada notificacao referencia `source_type` e `source_id`.
- Marcar como lida ou dispensada altera apenas a notificacao.
- A geracao local deve ser idempotente para a mesma origem ativa.

Racional:

- O prompt de governanca pede notificacao proativa, mas sem esconder o dado que
  originou o alerta.
- Alertas precisam acelerar a operacao sem duplicar regras de negocio.
- Canais externos futuros devem consumir a mesma fila, preservando auditoria.

Consequencias:

- O Command Center pode priorizar o que merece atencao sem editar handoffs,
  campanhas ou OKRs.
- Fases futuras podem adicionar Slack/WhatsApp como adaptadores de entrega.
- Dedupe distribuido e preferencias por usuario ficam fora do MVP local.

## ADR-018 - Comparacao multi-workspace nasce como camada executiva

Data: 2026-07-20

Decisao:

- Criar workspaces em `organizations` e `company_profiles`.
- Calcular metricas executivas agrupadas por `org_id`.
- Guardar snapshots em `workspace_metric_snapshots`.
- Manter o restante do MVP local operando com o workspace interno enquanto a
  migracao multi-tenant completa nao chega.

Racional:

- O prompt pede comparar empresas/workspaces, mas reescrever todos os servicos
  para `org_id` dinamico de uma vez aumentaria risco e blast radius.
- Uma camada executiva ja cria valor e evidencia quais metricas precisam ser
  isoladas por workspace.
- Snapshots permitem acompanhar tendencia futura mesmo antes de grafico
  historico completo.

Consequencias:

- Workspaces recem-criados podem aparecer com zeros ate receberem dados.
- A UI deve deixar claro que a comparacao e executiva, nao troca de contexto
  operacional.
- Fases futuras devem remover gradualmente o `ORG_ID` fixo dos servicos.

## ADR-019 - Workspace ativo local migra dominios aos poucos

Data: 2026-07-20

Decisao:

- Persistir o workspace ativo local em `workspace_context`.
- Criar helper `current_org_id(conn)`.
- Migrar dominios de uso frequente por fase, em vez de trocar todos os
  servicos de uma vez.
- Documentar quais superficies ja respeitam o workspace ativo.

Racional:

- O MVP acumulou muitos servicos com `ORG_ID` fixo.
- Uma migracao ampla demais aumentaria risco de regressao no importador,
  campanhas, agente e auditoria.
- Contexto operacional visivel ja cria valor e permite validar o desenho de
  multi-tenancy antes de uma refatoracao completa.

Consequencias:

- Durante a transicao, algumas telas continuam operando no workspace interno.
- Testes de cada fase devem provar quais superficies foram migradas.
- A UI deve recarregar dados contextuais ao trocar workspace.

## ADR-020 - Experimentos comerciais seguem o workspace ativo

Data: 2026-07-20

Decisao:

- Leads de experimento e campanhas simuladas devem usar `current_org_id(conn)`.
- A UI nao envia `org_id` para escolher tenant operacional.
- Listas, campanhas, envios e eventos devem ser validados no backend contra o
  workspace ativo antes de qualquer criacao ou simulacao.

Racional:

- A Fase 17 tornou listas contextuais; o fluxo seguinte e transformar listas em
  leads e campanhas sem misturar empresas internas diferentes.
- O modulo ainda e simulado, mas ja representa risco operacional se gerar
  metricas ou supressoes no workspace errado.
- Validacao no backend mantem a decisao em trilho duro, nao em estado de UI.

Consequencias:

- Campanhas criadas antes da migracao permanecem vinculadas ao `org_id` salvo.
- Ao trocar workspace, campanhas e leads de outro workspace desaparecem das
  telas migradas.
- Sequencias e agente SDR ainda precisam de fases proprias de migracao.

## ADR-021 - Templates sao configuracao operacional do workspace

Data: 2026-07-20

Decisao:

- Templates de e-mail e suas versoes devem usar `current_org_id(conn)`.
- Renderizacao deve recusar template/version de outro workspace.
- Compartilhamento entre workspaces fica fora do caminho implicito e deve ser
  implementado no futuro como clonagem/acao auditavel.

Racional:

- Copy, tom de voz e variaveis padrao fazem parte da identidade operacional de
  cada empresa interna.
- Reutilizacao acidental de template entre workspaces pode gerar mensagem com
  tom, CTA ou oferta errados.
- O rodape de compliance continua injetado no backend, independente do
  workspace.

Consequencias:

- Ao trocar workspace, a aba `Templates` mostra apenas a biblioteca daquele
  contexto.
- Campanhas e sequencias futuras devem referenciar templates do mesmo workspace.
- Playbooks continuam sendo o caminho certo para reuso planejado entre empresas.

## ADR-022 - Sequencias sao maquina de estado por workspace

Data: 2026-07-20

Decisao:

- Sequencias, passos, jornadas, aprovacoes e logs de acao relacionados a
  cadencia devem usar `current_org_id(conn)`.
- Toda acao deve validar que os IDs recebidos pertencem ao workspace ativo.
- Templates de passos devem ser resolvidos pelo mesmo contexto ativo.

Racional:

- Cadencia e o ponto em que o sistema comeca a executar trabalho comercial ao
  longo do tempo, mesmo que ainda simulado.
- Misturar jornada/aprovacao de workspaces diferentes gera risco operacional e
  quebra confianca no Command Center.
- A Fase 19 ja isolou templates; sequencias precisam acompanhar essa fronteira.

Consequencias:

- Ao trocar workspace, jornadas e aprovacoes de outro contexto desaparecem da
  aba `Sequencias`.
- Fluxos de ICP, respostas e handoffs ainda precisam de fases dedicadas.
- O envio continua simulado e dependente de aprovacao humana.

## ADR-023 - ICP e fila SDR seguem o workspace ativo

Data: 2026-07-20

Decisao:

- Regras ICP e itens da fila de priorizacao SDR devem usar
  `current_org_id(conn)`.
- Priorizacao deve validar regra e lista contra o workspace ativo antes de
  avaliar candidatos ou criar leads.
- Decisoes humanas sobre sugestoes so podem atuar em itens do workspace ativo.

Racional:

- ICP define quem pode ser abordado; misturar regras entre empresas internas
  mudaria o alvo comercial e quebraria confianca operacional.
- A fila SDR alimenta cadencias e aprovacoes futuras, entao precisa nascer
  isolada antes de maior autonomia.
- O prompt do agente exige que ICP seja trilho estruturado de backend, nao
  julgamento livre do modelo nem estado de interface.

Consequencias:

- Ao trocar workspace, regras ICP e sugestoes SDR de outro contexto deixam de
  aparecer.
- Playbooks futuros poderao preencher ICPs, mas a aplicacao devera ser
  explicita e auditavel.
- Respostas, handoffs e reunioes ainda mantem migracoes dedicadas futuras.

## ADR-024 - Respostas, handoffs e reunioes seguem o workspace ativo

Data: 2026-07-20

Decisao:

- Classificacoes de resposta, handoffs e reunioes devem usar
  `current_org_id(conn)`.
- Acoes por `lead_id`, `send_id`, `handoff_id` ou `meeting_id` devem validar
  que o registro pertence ao workspace ativo.
- Opt-out e supressao seguem globais por e-mail enquanto o schema mantiver
  unicidade global de e-mail.

Racional:

- Resposta e reuniao sao parte do funil comercial de uma empresa interna
  especifica; atravessar workspace confundiria follow-up, agenda e compliance.
- Handoff e onde o humano toma decisao de valor alto, entao a fronteira de
  contexto precisa estar no backend.
- Supressao global prioriza seguranca de contato e evita reabordar alguem que
  pediu remocao em qualquer fluxo local.

Consequencias:

- Ao trocar workspace, respostas, handoffs e reunioes de outro contexto deixam
  de aparecer.
- Reunioes continuam registros locais auditaveis, sem calendario real.
- Replay e Command Center completo ainda podem exigir fases proprias para
  remover todos os usos remanescentes de `ORG_ID`.

## ADR-025 - Command Center e replay sao leituras do workspace ativo

Data: 2026-07-20

Decisao:

- `command_center` e `lead_timeline` devem usar `current_org_id(conn)`.
- Agregadores do Command Center nao devem materializar estado paralelo.
- `command_center_action` continua delegando para aprovacoes, handoffs e
  reunioes, que validam seus proprios IDs no workspace ativo.

Racional:

- A camada de comando precisa ser confiavel quando o operador troca de empresa
  interna; mostrar pendencias de outro workspace quebraria a promessa de
  transparencia.
- Como as tabelas de origem ja foram migradas por dominio, a agregacao deve
  apenas respeitar a fronteira e preservar `source_type`/`source_id`.
- Manter a acao delegada evita duplicar regras de negocio e guardrails.

Consequencias:

- Replay de lead fora do workspace ativo retorna vazio.
- A aba `Comando` passa a refletir o contexto operacional selecionado.
- Auditoria global e governanca/playbooks seguem com fases dedicadas futuras.

## ADR-026 - Governanca do agente e custo seguem o workspace ativo

Data: 2026-07-20

Decisao:

- Configuracoes do agente, simulacoes e custos devem usar
  `current_org_id(conn)`.
- Cada workspace recebe seu proprio default ativo ao abrir governanca pela
  primeira vez.
- Simulacoes e custos validam `config_version_id` e `lead_id` contra o
  workspace ativo.

Racional:

- Prompt, regras e status de ativacao podem mudar por empresa interna; uma
  configuracao ativa global confundiria comportamento e auditoria.
- Custo de IA precisa ser atribuivel por workspace para evitar surpresa
  operacional.
- A simulacao de staging so e confiavel se usar leads e regras do mesmo
  contexto.

Consequencias:

- Ao trocar workspace, versoes, simulacoes e custos de outro contexto deixam de
  aparecer.
- Defaults podem ter `version_number = 1` em cada workspace.
- Playbooks continuam com fase dedicada para aplicar configuracoes de agente.

## ADR-027 - Playbooks sao locais ao workspace ativo

Data: 2026-07-20

Decisao:

- Perfil de empresa, biblioteca de playbooks, versoes e aplicacao ativa devem
  usar `current_org_id(conn)`.
- Defaults de playbook sao idempotentes por workspace.
- Compartilhamento entre workspaces fica fora do caminho implicito e deve ser
  implementado como clonagem futura auditavel.

Racional:

- Playbook combina ICP, copy, cadencia, OKR e governanca; aplicar o pacote da
  empresa errada criaria erro comercial silencioso.
- O prompt de governanca pede reuso entre empresas, mas como acao explicita,
  nao vazamento automatico.
- Defaults por workspace aceleram onboarding sem misturar identidade comercial.

Consequencias:

- O mesmo nome de playbook pode existir em workspaces diferentes.
- Ao trocar workspace, biblioteca e aplicacao ativa mudam junto.
- Fase futura pode criar acao `clone_playbook_to_workspace` com auditoria.

## ADR-028 - Auditoria operacional segue o workspace ativo

Data: 2026-07-20

Decisao:

- A leitura de `audit_logs` pela API operacional deve usar
  `current_org_id(conn)`.
- A tela local de auditoria nao deve misturar eventos de empresas internas
  diferentes.
- Uma visao global administrativa fica fora do MVP local e deve ser criada
  como superficie explicita futura.

Racional:

- Auditoria e parte central da transparencia radical; mostrar eventos de outro
  workspace quebra a confianca do operador.
- A gravacao ja carrega `org_id`; a leitura precisa acompanhar a fronteira de
  contexto.
- Separar leitura operacional de leitura administrativa prepara RBAC futuro.

Consequencias:

- Ao trocar workspace, `/api/audit` acompanha a empresa ativa.
- Eventos globais/administrativos precisarao de endpoint proprio no futuro.
- Testes de contexto devem cobrir que eventos nao vazam entre workspaces.

## ADR-029 - Reuso de playbook entre empresas e clonagem auditavel

Data: 2026-07-20

Decisao:

- Playbooks nao serao compartilhados por referencia entre workspaces.
- Reuso entre empresas deve criar um novo playbook no workspace de destino.
- A clonagem preserva metadados de origem e exige acao explicita do operador.

Racional:

- O prompt de governanca pede biblioteca compartilhavel entre empresas suas,
  mas nao compartilhamento silencioso.
- Referencia compartilhada dificultaria auditoria e poderia alterar duas
  empresas com uma edicao futura.
- Clonagem cria um ponto de partida reaproveitavel sem quebrar isolamento.

Consequencias:

- O clone tem ciclo de versao independente a partir da versao 1.
- Aplicar o clone no destino continua sendo uma acao separada.
- Fases futuras podem comparar performance entre playbook original e clones
  por metadados de origem.

## ADR-030 - Onboarding compoe servicos existentes

Data: 2026-07-20

Decisao:

- O wizard de onboarding deve chamar os mesmos servicos usados manualmente:
  workspace, playbook, ICP, template, sequencia e OKR.
- O novo workspace se torna o contexto ativo ao fim do onboarding.
- O wizard nao cria envio real, leads automaticos ou cadencias sem aprovacao.

Racional:

- O prompt de governanca pede que uma nova empresa fique operacional rapido,
  mas sem perder transparencia e editabilidade.
- Duplicar logica de ICP/template/sequencia criaria divergencia e buracos nos
  trilhos duros.
- Tornar o workspace ativo imediatamente permite ao operador revisar o Command
  Center ja no contexto correto.

Consequencias:

- Cada artefato criado pelo wizard possui o mesmo modelo e auditoria do fluxo
  manual.
- O onboarding pode ser usado como base para um produto SaaS futuro, mas ainda
  e singleton/local nesta fase.
- Envio real continua fora do escopo ate infraestrutura e compliance completos.

## ADR-031 - Playbook gera plano antes de criar artefatos

Data: 2026-07-20

Decisao:

- Aplicar operacionalmente um playbook deve passar por um plano revisavel.
- O plano fica persistido em `playbook_execution_plans`.
- Criar o plano nao cria ICP, template, sequencia nem OKR; aplicar o plano sim.

Racional:

- O prompt de governanca pede transparencia radical e artefatos editaveis.
- Playbook mistura ICP, copy, cadencia e meta; criar tudo de uma vez sem
  preview reduziria confianca do operador.
- Separar preview de aplicacao preserva a promessa de humano no controle.

Consequencias:

- A UI pode mostrar impacto antes de criar artefatos.
- Planos aplicados viram trilha de auditoria para explicar configuracoes.
- Fases futuras podem adicionar edicao granular e aprovacao multiusuario.

## ADR-032 - Chaves de API nao guardam token em texto puro

Data: 2026-07-21

Decisao:

- Tokens de API devem ser retornados completos apenas na criacao.
- O banco guarda somente hash SHA-256, prefixo e mascara para exibicao.
- Creditos devem ser alterados por ledger append-only, com saldo negativo
  recusado no backend.

Racional:

- A camada SaaS futura precisa suportar uso programatico sem transformar o
  banco local em cofre de segredos reversiveis.
- Prefixo e mascara permitem suporte operacional sem expor credencial.
- Ledger de creditos torna cobranca e consumo auditaveis e evita "saldo magico"
  editado diretamente pela interface.

Consequencias:

- Operador precisa copiar o token no momento da criacao; depois ele nao sera
  recuperavel.
- Revogar chave preserva historico em vez de apagar registro.
- Fases futuras podem validar chave recebida por header comparando hash e podem
  debitar creditos usando a mesma funcao de ledger.

## ADR-033 - API publica usa org da chave, nao contexto da topbar

Data: 2026-07-21

Decisao:

- Endpoints publicos autenticados por API key devem resolver `org_id` a partir
  da chave ativa.
- Rate limit e creditos sao avaliados antes da regra de negocio do endpoint.
- O `workspace_context` local continua existindo apenas para a UI interna.

Racional:

- Integracoes programaticas nao podem mudar de workspace porque alguem trocou a
  topbar no localhost.
- O prompt SaaS pede cota no backend, nao apenas na interface.
- Registrar chamadas bloqueadas e bem-sucedidas cria auditoria para cobranca,
  suporte e investigacao de abuso.

Consequencias:

- Servicos publicos precisam aceitar o contexto da chave explicitamente.
- Chamadas bloqueadas por rate limit, escopo ou credito tambem entram em
  `api_usage_events`.
- A proxima fase pode documentar esses contratos em OpenAPI sem redesenhar os
  trilhos.

## ADR-034 - OpenAPI local e o contrato da API publica

Data: 2026-07-21

Decisao:

- O contrato da API publica deve ser exposto em JSON OpenAPI por endpoint local.
- A especificacao deve documentar escopo, custo em creditos e rate limit como
  extensoes `x-*`.
- A documentacao publica local nao consome creditos e nao exige chave de API.

Racional:

- A camada SaaS pede API REST documentada antes de planos comerciais.
- Integradores precisam descobrir o contrato antes de criar chamadas pagas.
- Custo e rate limit sao parte do comportamento de negocio, nao notas soltas em
  documentacao externa.

Consequencias:

- Novos endpoints publicos devem atualizar a especificacao no mesmo commit da
  implementacao.
- Testes passam a verificar a presenca dos contratos publicos essenciais.
- Uma futura Swagger UI pode reutilizar o mesmo JSON sem novo desenho de API.
