# Fase 36 - Score de empresa configuravel por workspace

## Objetivo

Permitir que cada workspace ajuste a interpretacao comercial do
`opportunity_score` sem alterar codigo e sem sobrescrever o score base global da
empresa. A fase transforma o score de empresa em uma camada configuravel e
explicavel, alinhada aos filtros, segmentos salvos e ICPs.

## Contexto

O `score_company` atual calcula um score base usando situacao cadastral,
presenca de contato, porte, capital social, idade da empresa e setor inferido
pelo CNAE. Esse default e util para uso interno, mas diferentes workspaces
podem priorizar sinais opostos:

- Nine pode valorizar mais saude, profissionais autonomos e empresas pequenas.
- Vagou pode valorizar RH, servicos e maturidade digital.
- Real Grana pode dar peso maior a capital social, financeiro e maturidade.

O prompt de governanca pede multi-tenancy real e transparencia sobre toda
inferenca. Por isso, a configuracao deve ser do workspace e a busca deve mostrar
quando o score exibido veio da camada configurada.

## Escopo

- Criar configuracao ativa de score de empresa por workspace.
- Tornar `score_company` parametrizavel por regras JSON, mantendo o default
  atual quando nenhuma regra externa for enviada.
- Criar tabela de score calculado por workspace e empresa.
- Recalcular em lote controlado para o workspace ativo.
- Usar o score do workspace na busca e na priorizacao ICP quando existir.
- Expor endpoints internos e painel local de configuracao.
- Cobrir defaults, customizacao, isolamento e recalculo com testes.

## Fora do escopo desta fase

- Versionamento completo de configuracoes antigas.
- Score diferente por ICP dentro do mesmo workspace.
- Recalculo assincrono em fila.
- Migracao para Postgres.
- Explicacao visual linha a linha em editor avancado.

## Modelo de dados

Nova tabela `workspace_company_score_configs`:

- `org_id`: workspace dono.
- `name`: nome operacional da configuracao.
- `status`: `active` ou `archived`.
- `rules_json`: objeto com pesos do score de empresa.
- `created_at`, `updated_at`.

Nova tabela `company_workspace_scores`:

- `org_id`: workspace dono do score.
- `company_id`: empresa pontuada.
- `scoring_config_id`: configuracao usada.
- `opportunity_score`: score calculado para o workspace.
- `score_reasons_json`: explicacoes do score calculado.
- `scored_at`: timestamp do recalculo.

Essa separacao evita que um workspace sobrescreva o score operacional do outro.
`companies.opportunity_score` continua sendo o score base cadastral.

## Regras configuraveis

Default proposto, equivalente ao algoritmo atual:

- `base_score`: 20.
- `status.active_bonus`: 20.
- `status.inactive_penalty`: -15.
- `contact.email_bonus`: 15.
- `contact.phone_bonus`: 8.
- `size_bonus`: ME/EPP/MEDIO/GRANDE = 8, DEMAIS = 6.
- `capital_bonus`: faixas de 1.000.000, 100.000 e 10.000.
- `age_bonus`: menos de 2 anos, ate 10 anos e consolidada.
- `sector_bonus`: Tecnologia, Saude, Servicos profissionais e Financeiro = 7.

Os valores devem ser validados dentro de uma faixa conservadora, e o score final
continua limitado entre 0 e 100.

## Contratos internos

- `GET /api/scoring/company-config`
  - Retorna a configuracao ativa do workspace.
- `POST /api/scoring/company-config`
  - Atualiza `name` e `rules` da configuracao ativa.
- `POST /api/scoring/company-rescore`
  - Recalcula scores para o workspace ativo.
  - Aceita `limit` e opcionalmente `list_id`.

## Aplicacao no produto

- A busca de empresas usa `company_workspace_scores` quando houver score para o
  workspace ativo e cai para `companies.opportunity_score` quando nao houver.
- O filtro `min_score` usa o mesmo `COALESCE`.
- O detalhe da empresa exibe os motivos do score do workspace quando existir.
- A priorizacao ICP usa o score do workspace quando existir, preservando o
  comportamento antigo como fallback.

## Criterios de aceite

- Default de score de empresa e criado automaticamente por workspace.
- `score_company` puro continua retornando o mesmo comportamento default.
- Customizar bonus de setor altera o score recalculado sem alterar o score base
  global da empresa.
- Workspace secundario nao herda configuracao nem scores recalculados do
  workspace interno.
- Busca, detalhe e priorizacao ICP enxergam o score do workspace quando ele
  existir.
- UI permite salvar regras JSON e disparar recalculo controlado.
