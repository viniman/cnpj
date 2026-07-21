# Fase 25 - Playbooks por workspace ativo

## Objetivo

Migrar biblioteca de playbooks, versoes e aplicacao ativa para o workspace
ativo. Cada empresa interna deve ter perfil, playbooks default e aplicacao
ativa proprios, sem compartilhamento implicito.

## Escopo

- Migrar para `current_org_id(conn)`:
  - `ensure_company_profile`
  - `ensure_default_playbooks`
  - `get_playbook`
  - `list_playbooks`
  - `create_playbook`
  - `create_playbook_version`
  - `active_playbook_application`
  - `apply_playbook`
  - `playbook_library`
- Validar que `playbook_id` e `version_id` pertencem ao workspace ativo.
- Garantir default idempotente por workspace.
- Cobrir isolamento multi-workspace com testes automatizados.

## Fora do escopo desta fase

- Clonar playbook entre workspaces.
- Aplicar playbook criando automaticamente ICP, templates ou sequencias.
- RBAC para edicao de playbooks.

## Decisao central

Playbook e uma referencia operacional do workspace. O reuso entre empresas deve
ser uma acao explicita futura de clonagem/aplicacao auditavel; por enquanto,
cada workspace ganha seus defaults e sua aplicacao ativa local.

## Implementado nesta fase

- `ensure_company_profile` agora resolve o perfil pelo workspace ativo.
- Default de playbook e criado por workspace ativo e permanece idempotente.
- Criacao, listagem e detalhe de playbooks usam `current_org_id(conn)`.
- Criacao de versao valida que o playbook pertence ao workspace ativo.
- Aplicacao de playbook valida o playbook/versao no workspace ativo.
- Aplicacao ativa e historico de aplicacoes sao filtrados por `org_id`.
- Auditoria de criacao, versao e aplicacao e registrada no workspace ativo.
- Teste multi-workspace cobre biblioteca, defaults, versionamento e aplicacao.

## Criterios de aceite

- Workspace secundario cria perfil e playbook default proprios.
- Listagem nao mostra playbooks de outro workspace.
- Criar playbook com mesmo nome e permitido em workspaces diferentes.
- Versionar playbook de outro workspace e recusado.
- Aplicar playbook ou versao de outro workspace e recusado.
- Aplicacao ativa retorna apenas o workspace ativo.
- Testes automatizados provam isolamento entre workspace interno e secundario.
