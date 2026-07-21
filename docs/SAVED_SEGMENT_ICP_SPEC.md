# Fase 34 - Segmentos salvos e conversao para ICP

## Objetivo

Fechar o fluxo de uso descrito nos prompts de growth: uma combinacao de filtros
da tela de empresas deve virar um segmento reutilizavel e, quando fizer sentido,
uma regra ICP estruturada para alimentar a fila SDR.

## Contexto

O schema ja possuia `saved_filters`, mas a tabela ainda nao estava ligada a
servicos, API ou UI. A plataforma tambem ja possui `icp_rules` e
`lead_priority_queue`. Esta fase conecta a pesquisa operacional ao funil SDR,
sem criar um segundo conceito de ICP.

## Escopo

- Persistir filtros de empresas em `saved_filters` no workspace ativo.
- Validar e normalizar filtros aceitos pela busca.
- Guardar contagem de empresas no momento da criacao do segmento.
- Listar segmentos do workspace ativo.
- Aplicar um segmento salvo de volta na tela de empresas.
- Converter segmento salvo em `icp_rules`.
- Auditar criacao de segmento e conversao para ICP.
- Expor endpoints internos locais.
- Mostrar controles na tela `Empresas`.

## Fora do escopo desta fase

- Compartilhamento de segmentos entre workspaces.
- Versionamento completo de segmento.
- Atualizacao automatica de contagem em background.
- Excluir segmentos.
- Criar campanha ou sequencia diretamente a partir do segmento.

## Modelo de dados

Reusa `saved_filters`:

- `org_id`: workspace ativo.
- `name`: nome do segmento.
- `filters_json`: payload normalizado com filtros aceitos pela busca.
- `created_at`: criacao.

Como a tabela ja existia, a contagem no momento da criacao fica em
`filters_json._snapshot.total`. Isso evita migracao destrutiva nesta fase e
mantem compatibilidade com registros antigos.

## Filtros suportados

- `query`
- `state`
- `city`
- `cnae`
- `status`
- `size`
- `sector`
- `has_email`
- `has_phone`
- `min_score`

`limit` e `offset` nao fazem parte do segmento, porque segmento descreve o
mercado-alvo e nao a paginacao da tela.

## Conversao para ICP

Um segmento pode virar ICP usando os mesmos servicos ja existentes:

- `state` vira `states`.
- `city` vira `cities`.
- `cnae` vira `target_cnaes`.
- `size` vira `sizes`.
- `sector` vira `sectors`.
- `min_score` vira `min_company_score`.
- `has_email` vira `requires_email = true`.

Filtros textuais como `query` e `status` sao preservados em `source_filters`,
mas nao viram bloqueio duro na priorizacao atual quando nao ha campo
equivalente.

## Endpoints

- `GET /api/saved-filters`
- `POST /api/saved-filters`
- `POST /api/saved-filters/{id}/icp`

## Criterios de aceite

- Criar segmento salva filtros normalizados no workspace ativo.
- Segmento guarda contagem de empresas no momento da criacao.
- Listagem de segmentos nao vaza entre workspaces.
- Converter segmento cria uma regra ICP no workspace ativo.
- Conversao preserva filtros originais em `criteria.source_filters`.
- UI permite salvar filtros atuais, aplicar segmento e criar ICP.
