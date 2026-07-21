# PR local - Fase 33: Planos e modelo comercial validavel

## Objetivo

Adicionar um catalogo local de planos SaaS e assinatura por workspace, usando o
ledger de creditos existente para conceder creditos de plano de forma auditavel.

## Implementado

- [x] Documento `docs/SAAS_PLAN_MODEL_SPEC.md`.
- [x] ADR do catalogo local de planos e assinatura sem gateway.
- [x] Tabelas `saas_plans` e `workspace_plan_subscriptions`.
- [x] Defaults idempotentes de planos.
- [x] Servico para aplicar plano ao workspace ativo.
- [x] Concessao de creditos via `credit_transactions`.
- [x] Agregado `GET /api/saas/account` com planos e assinatura.
- [x] Endpoint `POST /api/saas/plan-subscription`.
- [x] UI no painel `SaaS e API`.
- [x] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saas_plans
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [x] Planos default existem e sao idempotentes.
- [x] Aplicar plano cria assinatura ativa.
- [x] Creditos incluidos sao registrados pelo ledger.
- [x] Troca de plano cancela assinatura anterior.
- [x] Plano arquivado e recusado.
- [x] SaaS account retorna plano atual e catalogo.
- [x] UI mostra assinatura e permite aplicar plano.
