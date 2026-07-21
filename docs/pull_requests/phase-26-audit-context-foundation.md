# PR local - Fase 26: Audit context foundation

Branch: `feature/26-audit-context-foundation`

Base local: `master`

## Objetivo

Migrar a leitura de auditoria operacional para o workspace ativo, evitando que
eventos de uma empresa interna aparecam quando outra estiver selecionada.

## Implementado

- Especificacao da fase em `docs/AUDIT_CONTEXT_SPEC.md`.
- ADR-028 definindo auditoria operacional como leitura do workspace ativo.
- `audit_events` usando `current_org_id(conn)`.
- `/api/audit` mantendo o contrato HTTP e respeitando a empresa ativa.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] `/api/audit` e `audit_events` leem `current_org_id(conn)`.
- [x] Trocar para workspace secundario oculta eventos do workspace interno.
- [x] Evento criado no workspace secundario aparece apenas quando ele esta ativo.
- [x] Voltar ao workspace interno restaura seus eventos de auditoria.
- [x] Teste automatizado prova isolamento de leitura.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_context
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 74 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- Uma visao global administrativa de auditoria continua fora do escopo e deve
  nascer futuramente com RBAC.
