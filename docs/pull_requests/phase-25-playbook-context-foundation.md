# PR local - Fase 25: Playbook context foundation

Branch: `feature/25-playbook-context-foundation`

Base local: `master`

## Objetivo

Migrar biblioteca de playbooks, versoes, perfil operacional e aplicacao ativa
para o workspace ativo, evitando reuso implicito entre empresas internas.

## Implementado

- Especificacao da fase em `docs/PLAYBOOK_CONTEXT_SPEC.md`.
- ADR-027 definindo playbooks como dominio do workspace ativo.
- Perfil operacional resolvido pelo workspace ativo.
- Default de playbook criado de forma idempotente por workspace.
- Criacao, listagem e detalhe de playbooks por workspace ativo.
- Versionamento recusando playbook de outro workspace.
- Aplicacao recusando playbook ou versao de outro workspace.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Workspace secundario cria perfil e playbook default proprios.
- [x] Listagem nao mostra playbooks de outro workspace.
- [x] Criar playbook com mesmo nome e permitido em workspaces diferentes.
- [x] Versionar playbook de outro workspace e recusado.
- [x] Aplicar playbook de outro workspace e recusado.
- [x] Aplicacao ativa retorna apenas o workspace ativo.
- [x] Testes automatizados provam isolamento entre dois workspaces.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_playbooks
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 73 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- Clonar playbook entre workspaces continua fora do escopo e deve ser uma acao
  futura explicita, auditavel e nao automatica.
