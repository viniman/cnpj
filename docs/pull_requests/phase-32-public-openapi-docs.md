# PR local - Fase 32: Documentacao OpenAPI da API publica

## Objetivo

Publicar um contrato OpenAPI local para a API publica de empresas, tornando
explícitos autenticacao, filtros, custo em creditos, rate limit e erros
esperados.

## Implementado

- [ ] Documento `docs/PUBLIC_OPENAPI_SPEC.md`.
- [ ] ADR registrando a decisao de OpenAPI local como contrato da API publica.
- [ ] Endpoint `GET /api/public/openapi.json`.
- [ ] Esquemas OpenAPI para empresa, resultado de busca, uso e erro.
- [ ] Extensoes `x-required-scope`, `x-credit-cost` e
  `x-rate-limit-default-per-minute`.
- [ ] Link/contrato visivel no painel `SaaS e API`.
- [ ] Testes automatizados da especificacao.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_public_openapi
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [ ] OpenAPI JSON retorna dados validos.
- [ ] `GET /api/public/companies` aparece na especificacao.
- [ ] Autenticacao por `X-API-Key` e Bearer esta documentada.
- [ ] Custo, escopo e rate limit aparecem no contrato.
- [ ] Erros 401, 402, 403 e 429 aparecem no contrato.
- [ ] UI interna mostra o contrato para o operador.
