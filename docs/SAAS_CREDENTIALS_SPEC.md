# Fase 30 - Fundacao SaaS de chaves de API e creditos

## Objetivo

Criar a base local para transformar o MVP em SaaS monetizavel: chaves de API
por workspace, carteira de creditos e ledger de transacoes. Esta fase prepara
o backend para uma API publica futura sem ainda expor endpoints externos que
consumam creditos automaticamente.

## Escopo

- Criar tabelas `api_keys`, `credit_wallets` e `credit_transactions`.
- Gerar chaves de API com token retornado apenas uma vez.
- Armazenar somente hash do token, prefixo e mascara.
- Revogar chaves sem deletar historico.
- Criar carteira idempotente por workspace ativo.
- Permitir credito/debito administrativo no ledger local.
- Impedir debito que deixaria saldo negativo.
- Expor API local para painel interno de credenciais e creditos.
- Expor UI simples no Command Center para criar/revogar chave e ajustar saldo.

## Fora do escopo desta fase

- Autenticacao real de usuario/sessao.
- API publica versionada para terceiros.
- Rate limit por janela de tempo.
- Consumo automatico de credito em busca/exportacao.
- Billing, checkout, nota fiscal ou integracao com gateway de pagamento.
- Planos comerciais editaveis.

## Decisao central

Creditos e chaves precisam nascer como trilhos de backend, nao como bloqueios de
interface. Mesmo no localhost, o token nunca deve ser salvo em texto puro e o
saldo deve ser alterado por ledger append-only. A fase seguinte podera aplicar
esse ledger em endpoints publicos e rate limits.

## Modelo de dados

- `api_keys`: `org_id`, nome, hash do token, prefixo, mascara, escopos,
  status, `last_used_at`, `created_at`, `revoked_at`.
- `credit_wallets`: uma carteira por `org_id`, saldo atual, plano local e
  timestamps.
- `credit_transactions`: ledger append-only com valor positivo/negativo,
  motivo, referencia, metadados e saldo apos a transacao.

## Criterios de aceite

- Token completo so aparece na resposta de criacao.
- Listagem mostra apenas mascara e prefixo.
- Revogar chave muda status e preserva registro.
- Carteira e criada uma unica vez por workspace.
- Credito aumenta saldo e grava transacao.
- Debito reduz saldo e grava transacao.
- Debito acima do saldo e recusado sem gravar transacao.
- Workspaces diferentes nao veem chaves, carteira nem transacoes entre si.
- Testes automatizados cobrem criacao, revogacao, ledger e isolamento.
