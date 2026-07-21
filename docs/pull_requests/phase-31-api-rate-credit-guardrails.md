# PR local - Fase 31: API rate and credit guardrails

Branch: `feature/31-api-rate-credit-guardrails`

Base local: `master`

## Objetivo

Aplicar, no backend, os trilhos de autenticação por API key, escopo, rate limit
e consumo de creditos para um endpoint publico local de busca de empresas.

## Implementado

- Especificacao da fase em `docs/API_RATE_CREDIT_SPEC.md`.
- ADR-033 definindo que API publica usa o `org_id` da chave, nao a topbar.
- Tabela `api_usage_events`.
- Guardrail `authorize_api_request`.
- Endpoint `GET /api/public/companies`.
- Debito de 1 credito em chamada bem-sucedida.
- Bloqueios por token ausente/invalido, escopo, saldo e rate limit.
- Uso recente exposto no painel `SaaS e API`.
- Testes automatizados cobrindo autenticacao, escopo, credito, rate limit e
  isolamento por workspace da chave.

## Checklist de aceite

- [x] Chamada sem token e recusada com 401.
- [x] Chave revogada e recusada.
- [x] Chave sem escopo exigido e recusada.
- [x] Chamada sem creditos suficientes e recusada sem debito.
- [x] Chamada bem-sucedida debita 1 credito e registra uso.
- [x] Rate limit por chave bloqueia excesso em janela de 60 segundos.
- [x] Endpoint publico de empresas usa os filtros ja existentes.
- [x] Uso recente aparece no agregado SaaS interno.
- [x] Testes automatizados cobrem autenticacao, escopo, credito, rate limit e
  isolamento por workspace da chave.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_api_rate_credit
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 90 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- Rate limit ainda e local/SQLite. Em SaaS real, a evolucao natural e Upstash
  Redis/QStash ou mecanismo equivalente serverless-friendly.
