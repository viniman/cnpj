# Fase 29 - Plano de execucao guiada de playbook

## Objetivo

Transformar um playbook aplicado em uma proposta operacional revisavel antes
de criar ICP, template, sequencia e OKR. O operador deve conseguir ver o que
sera criado, entender o impacto e aplicar explicitamente.

## Escopo

- Criar tabela `playbook_execution_plans`.
- Criar plano a partir de playbook e versao do workspace ativo.
- Gerar proposta estruturada para:
  - aplicacao do playbook;
  - ICP;
  - template de primeiro contato;
  - sequencia semi-supervisionada;
  - OKR inicial.
- Registrar um `diff_json` simples com contagens atuais e artefatos propostos.
- Aplicar plano por acao explicita, criando artefatos pelos servicos existentes.
- Bloquear plano de outro workspace.
- Bloquear reaplicacao de plano ja aplicado.
- Expor API local e painel simples na UI.

## Fora do escopo desta fase

- Edicao granular do plano antes da aplicacao.
- Diff semantico linha a linha de texto de template.
- Atualizar artefatos existentes; esta fase cria novos artefatos.
- Envio real ou inscricao automatica de leads.
- Aprovacao multiusuario/RBAC.

## Decisao central

Playbook nao deve alterar operacao de forma invisivel. Entre escolher um
playbook e criar artefatos operacionais existe um plano explicito, auditavel e
aplicado por humano. A aplicacao continua usando os mesmos servicos de ICP,
template, sequencia e OKR, preservando compliance e aprovacao humana.

## Implementado nesta fase

- Tabela `playbook_execution_plans` com plano, diff, status e artefatos criados.
- Servicos para criar, listar, buscar e aplicar planos no workspace ativo.
- API local:
  - `GET /api/playbook-execution-plans`
  - `POST /api/playbooks/{id}/execution-plans`
  - `POST /api/playbook-execution-plans/{id}/apply`
- UI no painel de Playbooks para criar plano, revisar criacoes/guardrails e
  aplicar rascunhos explicitamente.
- Auditoria para criacao e aplicacao de plano.
- Testes cobrindo preview sem efeitos colaterais, aplicacao unica e isolamento
  entre workspaces.

## Criterios de aceite

- Criar plano nao cria ICP, template, sequencia nem OKR.
- Plano mostra playbook, versao, proposta e diff simples.
- Aplicar plano cria os artefatos no workspace ativo.
- Sequencia criada exige aprovacao humana.
- Plano aplicado registra artefatos criados.
- Reaplicar plano aplicado e recusado.
- Plano de outro workspace e recusado.
- Testes automatizados cobrem preview, aplicacao e isolamento.
