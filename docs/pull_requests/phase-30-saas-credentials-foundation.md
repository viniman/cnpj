# PR local - Fase 30: SaaS credentials foundation

Branch: `feature/30-saas-credentials-foundation`

Base local: `master`

## Objetivo

Criar a fundacao SaaS local para chaves de API por workspace, carteira de
creditos e ledger auditavel, preparando a plataforma para API publica, rate
limit e consumo de creditos nas fases seguintes.

## Implementado

- Especificacao da fase em `docs/SAAS_CREDENTIALS_SPEC.md`.
- ADR-032 definindo que tokens nao sao armazenados em texto puro.
- Tabelas `api_keys`, `credit_wallets` e `credit_transactions`.
- Servicos para criar/listar/revogar chaves de API.
- Servicos de carteira e ledger com bloqueio de saldo negativo.
- Endpoints:
  - `GET /api/saas/account`
  - `POST /api/saas/api-keys`
  - `POST /api/saas/api-keys/{id}/revoke`
  - `POST /api/saas/credits/adjust`
- Painel `SaaS e API` no Command Center.
- Testes automatizados cobrindo token, revogacao, ledger e isolamento.

## Checklist de aceite

- [x] Token completo so aparece na resposta de criacao.
- [x] Listagem mostra apenas mascara e prefixo.
- [x] Revogar chave muda status e preserva registro.
- [x] Carteira e criada uma unica vez por workspace.
- [x] Credito aumenta saldo e grava transacao.
- [x] Debito reduz saldo e grava transacao.
- [x] Debito acima do saldo e recusado sem gravar transacao.
- [x] Workspaces diferentes nao veem chaves, carteira nem transacoes entre si.
- [x] Testes automatizados cobrem criacao, revogacao, ledger e isolamento.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saas_credentials
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 84 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- Esta fase nao debita busca/exportacao automaticamente; a fase seguinte deve
  aplicar rate limit e consumo de creditos nos endpoints publicos.
