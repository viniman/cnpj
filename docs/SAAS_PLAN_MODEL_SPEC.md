# Fase 33 - Planos e modelo comercial validavel

## Objetivo

Transformar a carteira de creditos e a API key local em um modelo comercial
validavel por workspace: catalogo de planos, assinatura local, limites
operacionais e concessao auditavel de creditos usando o ledger ja existente.

## Contexto

A fase 30 criou chaves de API e carteira de creditos. A fase 31 aplicou
credito e rate limit no endpoint publico. A fase 32 documentou esse contrato em
OpenAPI. Esta fase cria a camada comercial minima para testar preco, pacote e
limites antes de qualquer gateway de pagamento.

## Calibracao de mercado

Pesquisa feita em 2026-07-21 para calibracao, nao copia direta:

- Snov.io publica planos com creditos para busca/verificacao e destinatarios
  para campanhas: https://snov.io/pricing
- Casa dos Dados apresenta planos e API REST para consultas de CNPJ:
  https://portal.casadosdados.com.br/planos
- Econodata posiciona plataforma premium de prospeccao B2B:
  https://contrate.econodata.com.br/prospectar-planos-e-precos
- Fontes secundarias brasileiras citam Speedio a partir de faixas mensais mais
  altas; validar direto comercialmente antes de usar em material publico.

## Escopo

- Criar tabela `saas_plans` com catalogo local de planos.
- Criar tabela `workspace_plan_subscriptions` para assinatura ativa por
  workspace.
- Criar defaults idempotentes de planos.
- Permitir aplicar plano ao workspace ativo.
- Aplicar concessao de creditos do plano via `credit_transactions`, sem editar
  saldo diretamente.
- Atualizar `credit_wallets.plan_name` quando o plano muda.
- Expor planos e assinatura em `GET /api/saas/account`.
- Expor endpoint interno `POST /api/saas/plan-subscription`.
- Mostrar planos, limites e assinatura atual no painel `SaaS e API`.

## Fora do escopo desta fase

- Checkout real, recorrencia bancaria, nota fiscal ou gateway de pagamento.
- Aplicar automaticamente `max_api_keys` e rate limit por plano nos endpoints.
- Cupons, descontos, trial com expiracao automatica.
- Billing por destinatario unico em campanhas reais.
- Webhook de pagamento.

## Planos default

| Codigo | Preco mensal | Creditos incluidos | API/min | Chaves | Uso proposto |
|---|---:|---:|---:|---:|---|
| `free` | R$ 0 | 0 | 0 | 0 | Busca basica interna sem API publica |
| `starter` | R$ 197 | 1.000 | 60 | 2 | Validar API e listas pequenas |
| `growth` | R$ 497 | 5.000 | 120 | 5 | Operacao B2B com enrichment e exportacao |
| `scale` | R$ 997 | 20.000 | 240 | 10 | Uso mais intensivo com agente e campanhas |
| `internal` | R$ 0 | 10.000 | 600 | 20 | Uso proprio em localhost e testes internos |

Valores estao em centavos no banco (`monthly_price_brl_cents` e
`overage_credit_price_brl_cents`) para evitar erro de ponto flutuante em
calculo financeiro futuro.

## Modelo de dados

### `saas_plans`

- `code`: identificador estavel (`starter`, `growth`, etc.).
- `name`: nome exibivel.
- `status`: `active` ou `archived`.
- `monthly_price_brl_cents`: preco mensal em centavos.
- `included_credits`: creditos concedidos ao aplicar o plano.
- `api_rate_limit_per_minute`: limite recomendado por chave.
- `max_api_keys`: limite operacional recomendado.
- `allow_public_api`, `allow_exports`, `allow_enrichment`, `allow_agent`,
  `allow_campaigns`: flags de produto.
- `overage_credit_price_brl_cents`: preco do credito adicional.
- `metadata_json`: hipoteses e notas comerciais.
- `created_at`, `updated_at`.

### `workspace_plan_subscriptions`

- `org_id`: workspace assinante.
- `plan_id`: plano aplicado.
- `status`: `active`, `canceled` ou `expired`.
- `billing_period`: `monthly`, `annual` ou `internal`.
- `started_at`, `renews_at`, `canceled_at`.
- `metadata_json`: fonte da aplicacao, nota e ids de transacao.

Cada workspace deve ter no maximo uma assinatura ativa. Trocar de plano cancela
a assinatura ativa anterior e cria uma nova.

## Regras de aplicacao

1. Plano precisa existir e estar ativo.
2. O workspace ativo recebe uma nova assinatura `active`.
3. Qualquer assinatura ativa anterior do mesmo workspace vira `canceled`.
4. Se o plano tiver `included_credits > 0`, o sistema cria transacao positiva no
   ledger com `reference_type = 'saas_plan_subscription'`.
5. `credit_wallets.plan_name` passa a usar o `code` do plano.
6. A aplicacao e auditada em `audit_logs`.

## Criterios de aceite

- Defaults de planos sao criados de forma idempotente.
- `saas_account` retorna `plans`, `subscription`, `wallet`, `transactions`,
  `api_keys` e `usage_events`.
- Aplicar plano ativo cria assinatura e atualiza `wallet.plan_name`.
- Creditos incluidos entram pelo ledger e preservam saldo anterior.
- Trocar de plano cancela a assinatura ativa anterior.
- Plano arquivado nao pode ser aplicado.
- Workspaces diferentes nao veem assinatura um do outro.
- UI interna permite escolher plano e aplicar localmente.
