# PR local - Fase 18: Experiment context foundation

Branch: `feature/18-experiment-context-foundation`

Base local: `master`

## Objetivo

Migrar o modulo de experimentos comerciais simulados para o workspace ativo,
fechando o fluxo lista qualificada -> leads -> campanha -> simulacao -> evento
sem misturar empresas/workspaces internos.

## Implementado

- Especificacao da fase em `docs/EXPERIMENT_CONTEXT_SPEC.md`.
- ADR-020 definindo que experimentos seguem o workspace ativo.
- Supressoes e opt-outs consultados globalmente pelo modulo de higiene, por
  seguranca e compatibilidade com o schema atual de e-mail unico.
- `add_suppression` auditando no workspace ativo.
- `create_leads_from_list` validando lista pelo workspace ativo.
- `list_experiment_leads` filtrando pelo workspace ativo.
- `create_campaign`, `list_campaigns` e `get_campaign` usando workspace ativo.
- `simulate_campaign` bloqueando campanha/lista fora do workspace ativo.
- `record_campaign_event` bloqueando envio fora do workspace ativo.
- Funil de campanha calculado com escopo do workspace ativo.
- Aba `Experimentos` recarregando listas ao trocar workspace.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Lead criado a partir de lista recebe `org_id` do workspace ativo.
- [x] Listagem de leads retorna apenas leads do workspace ativo.
- [x] Campanha criada recebe `org_id` do workspace ativo.
- [x] Listagem e detalhe de campanha respeitam o workspace ativo.
- [x] Simulacao recusa campanha/lista fora do workspace ativo.
- [x] Evento de campanha recusa envio fora do workspace ativo.
- [x] Funil de campanha e calculado apenas para campanha do workspace ativo.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
python -m unittest tests.test_email_experiments
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 65 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O provider continua `simulated`; envio real via SES segue fora de escopo.
- Supressao permanece conservadora/global na leitura por causa do schema atual
  com `email UNIQUE`.
- Templates, sequencias, ICP, respostas e reunioes ainda exigem fases proprias
  de migracao para `current_org_id(conn)`.
