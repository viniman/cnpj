# PR local - Fase 24: Agent governance context foundation

Branch: `feature/24-agent-governance-context-foundation`

Base local: `master`

## Objetivo

Migrar governanca do agente e custos de IA para o workspace ativo, evitando que
configuracoes, simulacoes ou custos de uma empresa interna aparecam em outra.

## Implementado

- Especificacao da fase em `docs/AGENT_GOVERNANCE_CONTEXT_SPEC.md`.
- ADR-026 definindo governanca/custos como dominio do workspace ativo.
- Default ativo criado separadamente por workspace.
- Criacao, listagem e ativacao de configuracoes por workspace ativo.
- Simulacoes validando configuracao e lead do workspace ativo.
- Custos validando configuracao, lead, sequencia e acao do workspace ativo.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Workspace secundario nasce com default proprio.
- [x] Configuracao de outro workspace nao pode ser ativada.
- [x] Simulacao com configuracao/lead de outro workspace e recusada.
- [x] Custo com configuracao de outro workspace e recusado.
- [x] Listagens e resumo de custo mostram apenas o workspace ativo.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_agent_governance
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 72 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- Playbooks continuam com fase propria de migracao para `current_org_id(conn)`.
