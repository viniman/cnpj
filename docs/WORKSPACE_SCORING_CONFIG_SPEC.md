# Fase 35 - Motor de score configuravel por workspace

## Objetivo

Permitir que cada workspace ajuste a interpretacao comercial de e-mails sem
alterar codigo. O primeiro alvo e o dicionario de prefixos de e-mail, pedido no
prompt de growth como editavel por workspace.

## Contexto

O algoritmo `radar_cnpj.email_scoring.score_email` ja classifica e-mails por
prefixo, dominio pessoal/descartavel, match com socio, contato compartilhado e
supressao. Hoje os pesos de prefixos ficam fixos em `PREFIX_RULES`, o que e
bom para o default, mas ruim para workspaces com ICPs diferentes.

Exemplos:

- Uma empresa que vende para RH deve pontuar `rh@` melhor que o default.
- Uma empresa que vende para financeiro pode valorizar `financeiro@`.
- Uma operacao outbound mais conservadora pode rebaixar caixas genericas.

## Escopo

- Criar configuracao de scoring por workspace ativo.
- Criar default idempotente baseado no dicionario atual.
- Permitir atualizar regras de prefixo por API interna.
- Aplicar as regras do workspace em `score_email_record`.
- Persistir no resultado quais regras/configuracao foram usadas.
- Expor resumo na UI local.
- Cobrir isolamento multi-workspace com testes.

## Fora do escopo desta fase

- Versionamento historico completo de configuracoes.
- UI avancada com editor por linha para todos os prefixos.
- Recalculo em lote de todas as classificacoes antigas.
- Configuracao do `score_company`.
- Regras condicionais por ICP/campanha.

## Modelo de dados

Nova tabela `workspace_scoring_configs`:

- `org_id`: workspace dono.
- `name`: nome operacional da configuracao.
- `status`: `active` ou `archived`.
- `email_prefix_rules_json`: objeto `{prefixo: {area, score, label}}`.
- `thresholds_json`: thresholds futuros para elegibilidade/ICP.
- `created_at`, `updated_at`.

Somente uma configuracao ativa por workspace sera mantida nesta fase via
`UNIQUE(org_id, status)` no SQLite. Em versoes futuras isso deve virar
versionamento formal.

## Contratos internos

- `GET /api/scoring/config`
  - Retorna a configuracao ativa do workspace.
- `POST /api/scoring/config`
  - Atualiza a configuracao ativa do workspace.
  - Aceita `name`, `email_prefix_rules` e `thresholds`.
  - Normaliza prefixos para ASCII/lowercase.
  - Valida scores entre 0 e 100.

## Aplicacao no score

`score_email_record` deve carregar a configuracao ativa do workspace e passar
as regras para `score_email`. O algoritmo puro continua funcionando sem banco:
quando nenhuma regra customizada e enviada, usa `PREFIX_RULES`.

Quando uma regra customizada for aplicada, o resultado deve incluir:

- `scoring_config_id`
- `scoring_config_name`
- `workspace_prefix_rules_applied = true`
- razao explicita quando o prefixo vier da configuracao do workspace.

## Criterios de aceite

- Default de scoring e criado automaticamente por workspace.
- Atualizar `rh@` para score alto muda a pontuacao persistida de `rh@empresa`.
- Workspace secundario nao herda customizacao do workspace interno.
- `score_email` puro continua compativel com testes existentes.
- UI mostra a configuracao ativa e permite salvar JSON de prefixos.
