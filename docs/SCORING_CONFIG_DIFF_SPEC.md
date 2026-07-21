# Fase 38 - Diff visual de configuracoes de score

## Objetivo

Mostrar, antes de qualquer rollback de score, quais campos mudariam entre a
configuracao ativa do workspace e uma versao historica escolhida. A fase
transforma snapshots versionados da fase 37 em uma comparacao legivel para o
operador, sem exigir leitura manual de JSON.

## Contexto

A fase 37 criou historico e rollback para configuracoes de score de e-mail e
de empresa. O rollback ja e auditavel, mas ainda falta a etapa de confianca
visual: entender o impacto de restaurar uma versao antiga antes de clicar no
botao.

O diff desta fase usa apenas snapshots ja salvos em
`workspace_score_config_versions`. Ele nao cria uma nova fonte de verdade e nao
edita configuracoes.

## Escopo

- Criar comparador deterministico de JSON para snapshots de score.
- Comparar uma versao historica contra a versao ativa do mesmo workspace e tipo.
- Expor endpoint interno para carregar o diff de uma versao.
- Mostrar resumo e tabela de mudancas na UI local.
- Usar o mesmo diff como confirmacao operacional antes de rollback.
- Preservar isolamento por workspace.

## Fora do escopo desta fase

- Comparacao estatistica de impacto em empresas ja recalculadas.
- Simulacao de re-score em lote antes de salvar configuracao.
- Diff de ICP, segmentos, playbooks, templates ou governanca do agente.
- RBAC real para restringir quem pode ver diff ou executar rollback.

## Contrato interno

`GET /api/scoring/config-versions/{id}/diff`

Retorna o diff entre a versao ativa atual e a versao informada:

- `version`: snapshot escolhido.
- `active_version`: snapshot ativo atual do mesmo tipo.
- `summary`: contagem de campos adicionados, removidos, alterados e iguais.
- `changes`: lista ordenada por caminho JSON com:
  - `path`: caminho legivel, por exemplo `email_prefix_rules.rh.score`.
  - `change_type`: `added`, `removed`, `changed` ou `unchanged`.
  - `before`: valor na versao ativa atual.
  - `after`: valor na versao escolhida.

Para rollback, a leitura correta e:

- `before`: configuracao ativa agora.
- `after`: configuracao que sera restaurada.

## Criterios de aceite

- O diff de e-mail identifica mudancas em regras de prefixo.
- O diff de empresa identifica mudancas em regras comerciais.
- Versoes de outro workspace nao podem ser comparadas pelo workspace ativo.
- A UI mostra resumo e campos alterados antes do rollback.
- O rollback continua criando nova versao ativa, sem alterar o contrato da fase
  37.
