# Fase 40 - PostgreSQL staging e plano COPY

Data: 2026-07-21

## Objetivo

Preparar a plataforma para carga nacional da Receita Federal em PostgreSQL sem
trocar o runtime local de SQLite nesta fase.

A fase entrega uma fundacao operacional que:

- descreve o schema bruto de staging da Receita;
- mapeia ZIPs oficiais ja baixados pela tela `Importacao`;
- gera comandos `psql \copy` reproduziveis para carga bruta;
- aponta arquivos oficiais ausentes, indisponiveis ou ainda nao baixados;
- preserva o MVP local atual funcionando em SQLite.

## Nao objetivo

- Migrar a aplicacao inteira para PostgreSQL.
- Adicionar dependencia de driver Postgres.
- Executar `COPY` automaticamente contra um banco real.
- Transformar dados staging em tabelas finais normalizadas.
- Rodar carga nacional completa dentro do processo HTTP local.

## Por que esta fase existe

Os prompts mestres pedem base nacional, filtros densos e backend escalavel. A
fase 39 ja criou checkpoints para validar importacao limitada em SQLite, mas a
base completa mensal da Receita tem varios GB e precisa de uma trilha de carga
mais propria:

1. baixar catalogo oficial e ZIPs;
2. carregar arquivos brutos em tabelas de staging;
3. validar contagens e formatos;
4. transformar staging em entidades finais;
5. manter importacao resumivel e auditavel.

Esta fase cobre os passos 2 e parte do passo 3 como artefato local, testavel e
versionado.

## Schema de staging

Schema Postgres sugerido: `receita_staging`.

Extensoes:

- `unaccent` para busca textual futura;
- `pg_trgm` para busca aproximada de razao social, fantasia e e-mail.

Tabelas brutas:

- `empresas_raw`
- `estabelecimentos_raw`
- `socios_raw`
- `cnaes_raw`
- `motivos_raw`
- `municipios_raw`
- `naturezas_raw`
- `paises_raw`
- `qualificacoes_raw`
- `simples_raw`

Todas as colunas oficiais entram como `text`. Colunas operacionais
`snapshot`, `chunk`, `source_file` e `loaded_at` ficam em todas as tabelas para
auditoria de carga.

## Plano COPY

O endpoint de plano deve ser somente leitura e offline. Ele usa os registros
de `source_files`, criados pelos fluxos oficiais de download/sync.

Contrato esperado:

- `snapshot`: snapshot usado no plano;
- `schema_name`: schema Postgres sugerido;
- `ddl_sql`: SQL completo de criacao de staging;
- `copy_plan`: comandos por arquivo disponivel;
- `missing_files`: arquivos oficiais esperados que ainda nao apareceram;
- `unavailable_files`: arquivos conhecidos, mas sem ZIP local baixado;
- `guardrails`: cuidados antes de executar em um banco real.

Cada item de `copy_plan` inclui:

- arquivo ZIP de origem;
- familia oficial detectada;
- chunk, quando aplicavel;
- tabela de destino;
- caminho CSV esperado apos extracao;
- comando de extracao via `python -m zipfile`;
- comando `psql \copy`.

## Guardrails

- Usar uma instancia Postgres dedicada para carga nacional.
- Executar `\copy` com usuario de manutencao, nao usuario da aplicacao final.
- Carregar staging em uma transacao por arquivo.
- Conferir contagem por tabela antes de transformar dados.
- Nao expor a UI de plano como automacao de envio ou scraping.
- Tratar e-mails como dado para prospeccao B2B com supressao/opt-out em toda
  etapa posterior.

## Criterios de aceite

- Existe modulo Python sem dependencia externa que gera DDL e plano COPY.
- Existe endpoint local para consultar o plano do snapshot.
- A UI de `Importacao` mostra resumo do plano e comandos principais.
- Testes cobrem classificacao de arquivos, SQL de staging e endpoint.
- Documentacao e historico registram a decisao de manter SQLite como laboratorio
  e Postgres como destino de escala.
