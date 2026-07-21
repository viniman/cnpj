# PR local - Fase 32: Documentacao OpenAPI da API publica

## Objetivo

Publicar um contrato OpenAPI local para a API publica de empresas, tornando
explícitos autenticacao, filtros, custo em creditos, rate limit e erros
esperados.

## Implementado

- [x] Documento `docs/PUBLIC_OPENAPI_SPEC.md`.
- [x] ADR registrando a decisao de OpenAPI local como contrato da API publica.
- [x] Endpoint `GET /api/public/openapi.json`.
- [x] Esquemas OpenAPI para empresa, resultado de busca, uso e erro.
- [x] Extensoes `x-required-scope`, `x-credit-cost` e
  `x-rate-limit-default-per-minute`.
- [x] Link/contrato visivel no painel `SaaS e API`.
- [x] Testes automatizados da especificacao.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_public_openapi
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [x] OpenAPI JSON retorna dados validos.
- [x] `GET /api/public/companies` aparece na especificacao.
- [x] Autenticacao por `X-API-Key` e Bearer esta documentada.
- [x] Custo, escopo e rate limit aparecem no contrato.
- [x] Erros 401, 402, 403 e 429 aparecem no contrato.
- [x] UI interna mostra o contrato para o operador.
