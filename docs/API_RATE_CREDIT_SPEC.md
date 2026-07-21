# Fase 31 - Rate limit e consumo de creditos por API key

## Objetivo

Transformar a fundacao SaaS da fase 30 em um trilho operacional real: uma
chave de API ativa deve autenticar uma chamada publica local, respeitar escopo,
passar por rate limit e consumir creditos no backend.

## Escopo

- Criar tabela `api_usage_events` para auditar chamadas aceitas e recusadas.
- Aceitar token por `X-API-Key` ou `Authorization: Bearer`.
- Validar chave ativa por hash de token.
- Validar escopo exigido por endpoint.
- Aplicar rate limit por chave em janela de 60 segundos.
- Bloquear chamada sem credito suficiente antes de executar o endpoint.
- Debitar creditos apenas em chamada bem-sucedida.
- Expor endpoint publico local `GET /api/public/companies`.
- Reutilizar filtros existentes de busca de empresas.
- Expor uso recente no painel SaaS interno.

## Fora do escopo desta fase

- OpenAPI/Swagger.
- Planos comerciais configuraveis.
- Rate limit distribuido em Redis/Upstash.
- Consumo por resultado exportado ou e-mail revelado.
- Autenticacao por usuario final ou OAuth.

## Decisao central

Credito e rate limit precisam ser aplicados antes da regra de negocio publica.
O endpoint publico nunca deve depender de `workspace_context`: o workspace vem
da chave de API validada. Isso evita que uma troca manual na topbar afete uma
integracao programatica.

## Modelo de dados

- `api_usage_events`: `org_id`, `api_key_id`, endpoint, escopo, custo,
  status, HTTP code, mensagem, janela de rate limit, metadados e timestamp.

## Criterios de aceite

- Chamada sem token e recusada com 401.
- Chave revogada e recusada.
- Chave sem escopo exigido e recusada.
- Chamada sem creditos suficientes e recusada sem debito.
- Chamada bem-sucedida debita 1 credito e registra uso.
- Rate limit por chave bloqueia excesso em janela de 60 segundos.
- Endpoint publico de empresas usa os filtros ja existentes.
- Uso recente aparece no agregado SaaS interno.
- Testes automatizados cobrem autenticacao, escopo, credito, rate limit e
  isolamento por workspace da chave.
