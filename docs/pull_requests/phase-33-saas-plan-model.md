# PR local - Fase 33: Planos e modelo comercial validavel

## Objetivo

Adicionar um catalogo local de planos SaaS e assinatura por workspace, usando o
ledger de creditos existente para conceder creditos de plano de forma auditavel.

## Implementado

- [ ] Documento `docs/SAAS_PLAN_MODEL_SPEC.md`.
- [ ] ADR do catalogo local de planos e assinatura sem gateway.
- [ ] Tabelas `saas_plans` e `workspace_plan_subscriptions`.
- [ ] Defaults idempotentes de planos.
- [ ] Servico para aplicar plano ao workspace ativo.
- [ ] Concessao de creditos via `credit_transactions`.
- [ ] Agregado `GET /api/saas/account` com planos e assinatura.
- [ ] Endpoint `POST /api/saas/plan-subscription`.
- [ ] UI no painel `SaaS e API`.
- [ ] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saas_plans
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [ ] Planos default existem e sao idempotentes.
- [ ] Aplicar plano cria assinatura ativa.
- [ ] Creditos incluidos sao registrados pelo ledger.
- [ ] Troca de plano cancela assinatura anterior.
- [ ] Plano arquivado e recusado.
- [ ] SaaS account retorna plano atual e catalogo.
- [ ] UI mostra assinatura e permite aplicar plano.
