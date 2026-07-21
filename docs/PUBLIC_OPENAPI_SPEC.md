# Fase 32 - Documentacao OpenAPI da API publica

## Objetivo

Transformar o endpoint publico local criado na fase 31 em um contrato
documentado e verificavel por maquina, preparando a camada SaaS para
integracoes programaticas futuras sem redesenhar autenticacao, creditos ou rate
limit.

## Escopo

- Expor um documento OpenAPI JSON local.
- Documentar autenticacao por `X-API-Key` e `Authorization: Bearer`.
- Documentar o endpoint `GET /api/public/companies`.
- Explicitar escopo exigido, custo em creditos e rate limit padrao.
- Documentar parametros de filtro aceitos pela busca publica.
- Documentar respostas de sucesso e erros esperados.
- Expor o link da especificacao no painel interno `SaaS e API`.
- Cobrir a especificacao com testes automatizados.

## Fora do escopo desta fase

- Swagger UI interativo.
- Novo endpoint publico alem de empresas.
- OAuth, login de usuarios externos ou RBAC publico.
- Planos comerciais configuraveis.
- Rate limit distribuido em Redis/Upstash.

## Endpoint da especificacao

`GET /api/public/openapi.json`

Este endpoint e publico local, nao consome creditos e nao exige chave de API,
porque sua funcao e permitir que integradores descubram o contrato antes de
executar chamadas pagas.

## Endpoint documentado

`GET /api/public/companies`

### Seguranca

Aceita uma das formas:

- Header `X-API-Key: <token>`
- Header `Authorization: Bearer <token>`

### Escopo exigido

`companies:read`

### Custo

`1` credito por chamada bem-sucedida.

Chamadas bloqueadas por token ausente/invalido, escopo, saldo ou rate limit sao
auditadas em `api_usage_events`, mas nao debitam creditos.

### Rate limit padrao

`60` requisicoes por minuto por chave de API.

### Parametros de busca

- `query`: texto livre em CNPJ, razao social, nome fantasia, cidade ou e-mail.
- `state`: UF.
- `city`: cidade.
- `cnae`: codigo ou trecho de CNAE.
- `status`: situacao cadastral.
- `size`: porte.
- `sector`: setor.
- `has_email`: `true` para exigir e-mail cadastral.
- `has_phone`: `true` para exigir telefone cadastral.
- `min_score`: score minimo de oportunidade.
- `limit`: limite de itens, com teto aplicado pelo backend.
- `offset`: deslocamento para paginacao simples.

### Respostas

- `200`: lista paginada de empresas e metadados de uso.
- `401`: token ausente, invalido ou revogado.
- `402`: saldo de creditos insuficiente.
- `403`: chave sem escopo necessario.
- `429`: rate limit excedido.

## Criterios de aceite

- `GET /api/public/openapi.json` retorna `openapi`, `info`, `paths`,
  `components.securitySchemes` e schemas.
- A especificacao contem `GET /api/public/companies`.
- A operacao declara custo, escopo e rate limit em extensoes `x-*`.
- Os parametros publicos de filtro aparecem no contrato.
- Os erros 401, 402, 403 e 429 aparecem no contrato.
- O painel SaaS mostra o caminho da especificacao e o endpoint publico.
