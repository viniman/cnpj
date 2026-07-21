# PR local - Fase 29: Plano de execucao guiada de playbook

Branch: `feature/29-playbook-execution-plan`

Base local: `master`

## Objetivo

Criar uma etapa revisavel entre selecionar um playbook e materializar ICP,
template, sequencia e OKR no workspace ativo, mantendo o humano no controle e
registrando o impacto operacional antes da aplicacao.

## Implementado

- Especificacao da fase em `docs/PLAYBOOK_EXECUTION_PLAN_SPEC.md`.
- ADR-031 definindo que playbook gera plano antes de criar artefatos.
- Tabela `playbook_execution_plans`.
- Servicos para criar, listar, buscar e aplicar planos.
- Endpoints:
  - `GET /api/playbook-execution-plans`
  - `POST /api/playbooks/{id}/execution-plans`
  - `POST /api/playbook-execution-plans/{id}/apply`
- UI no painel de Playbooks para criar plano, revisar diff/guardrails e aplicar
  rascunhos.
- Testes automatizados cobrindo preview, aplicacao unica e isolamento.

## Checklist de aceite

- [x] Criar plano nao cria ICP, template, sequencia nem OKR.
- [x] Plano mostra playbook, versao, proposta e diff simples.
- [x] Aplicar plano cria os artefatos no workspace ativo.
- [x] Sequencia criada exige aprovacao humana.
- [x] Plano aplicado registra artefatos criados.
- [x] Reaplicar plano aplicado e recusado.
- [x] Plano de outro workspace e recusado.
- [x] Testes automatizados cobrem preview, aplicacao e isolamento.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_playbook_execution_plans
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 80 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- O plano nao inscreve leads e nao envia e-mail; ele cria apenas artefatos de
  configuracao apos acao humana explicita.
