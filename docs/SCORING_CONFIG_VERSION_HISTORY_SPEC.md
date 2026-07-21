# Fase 37 - Historico e rollback de configuracoes de score

## Objetivo

Criar uma trilha auditavel de versoes para configuracoes de score do workspace,
cobrindo tanto score de e-mail quanto score de empresa. A fase permite
inspecionar versoes antigas e restaurar uma configuracao anterior sem editar o
banco manualmente.

## Contexto

As fases 35 e 36 tornaram pesos de score editaveis por workspace:

- `workspace_scoring_configs` para prefixos/thresholds de e-mail.
- `workspace_company_score_configs` para regras comerciais de empresa.

Isso aumenta a aderencia do produto a diferentes ICPs, mas tambem cria risco
operacional: uma mudanca ruim pode alterar priorizacao, listas e campanhas. Os
prompts de governanca pedem rollback simples, versionamento e explicabilidade
de configuracoes sensiveis.

## Escopo

- Criar historico versionado comum para os dois tipos de score.
- Registrar a versao default quando uma configuracao e criada.
- Criar nova versao a cada atualizacao de score de e-mail ou empresa.
- Expor listagem de versoes por API interna.
- Permitir rollback criando uma nova versao ativa baseada no snapshot antigo.
- Mostrar historico e acao de rollback na UI local.
- Registrar auditoria da criacao de versoes e rollback.

## Fora do escopo desta fase

- Diff visual JSON campo a campo.
- Comparacao estatistica de impacto antes/depois.
- Permissoes RBAC reais para bloquear rollback por perfil.
- Versionamento de ICP, KPI ou segmentos salvos.
- Rollback automatico de scores ja recalculados; apos rollback, o operador pode
  recalcular pela acao existente.

## Modelo de dados

Nova tabela `workspace_score_config_versions`:

- `org_id`: workspace dono.
- `config_type`: `email` ou `company`.
- `source_config_id`: id da configuracao ativa de origem.
- `version_number`: sequencial por workspace e tipo.
- `status`: `active` ou `archived`.
- `name`: nome operacional da configuracao naquele momento.
- `config_json`: snapshot completo da configuracao.
- `change_note`: motivo curto da versao.
- `created_at`, `activated_at`.

Somente uma versao ativa por `org_id + config_type` fica marcada como ativa. O
rollback nao reativa a linha antiga: ele cria uma nova versao ativa com o mesmo
snapshot, preservando a cronologia.

## Contratos internos

- `GET /api/scoring/config-versions`
  - Parametro opcional `type=email|company`.
  - Retorna versoes do workspace ativo.
- `POST /api/scoring/config-versions/{id}/rollback`
  - Restaura o snapshot da versao informada para a configuracao ativa.
  - Cria nova versao ativa com `change_note` de rollback.

## Criterios de aceite

- Configuracoes default de e-mail e empresa criam versao 1 automaticamente.
- Atualizar score de e-mail cria uma nova versao ativa e arquiva a anterior.
- Atualizar score de empresa cria uma nova versao ativa e arquiva a anterior.
- Rollback restaura o snapshot antigo criando uma nova versao ativa.
- Versoes nao vazam entre workspaces.
- UI mostra historico por tipo e permite acionar rollback.
