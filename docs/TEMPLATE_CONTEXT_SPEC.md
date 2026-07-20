# Fase 19 - Templates por workspace ativo

## Objetivo

Migrar a biblioteca de templates de e-mail para o workspace ativo do MVP local.
Templates, versoes e renderizacao devem respeitar `current_org_id(conn)`,
mantendo o rodape de compliance injetado pelo backend.

Esta fase fecha uma peca importante do fluxo de outbound: cada empresa interna
deve conseguir manter seu proprio tom/copy sem enxergar ou reutilizar templates
de outro workspace por acidente.

## Escopo

- Migrar para workspace ativo:
  - `create_email_template`;
  - `list_email_templates`;
  - `get_email_template`;
  - `create_email_template_version`;
  - `template_version_for_render`;
  - `render_email_template`.
- Garantir que template de outro workspace nao possa ser detalhado,
  versionado ou renderizado.
- Manter validacao de variaveis e bloqueio de edicao do rodape de compliance.
- Cobrir isolamento com testes automatizados.

## Fora do escopo desta fase

- Migrar ICP/priorizacao e respostas/handoffs/reunioes.
- Criar marketplace de templates compartilhados.
- Clonagem explicita de templates entre workspaces.
- Edicao visual avancada de e-mail.
- Envio real de e-mail.

## Decisao central

Templates de e-mail sao configuracao operacional do workspace ativo. A UI nao
deve escolher `org_id`; o backend deriva o contexto de `workspace_context`.
Compartilhar template entre empresas deve ser uma acao explicita futura, nao um
efeito colateral de lista global.

## Criterios de aceite

- Template criado recebe `org_id` do workspace ativo.
- Listagem retorna apenas templates do workspace ativo.
- Detalhe de template fora do workspace ativo retorna vazio.
- Nova versao so pode ser criada para template do workspace ativo.
- Renderizacao recusa template ou versao de outro workspace.
- Rodape de compliance continua injetado pelo backend.
- Testes automatizados provam isolamento entre dois workspaces.

## Implementado nesta fase

- `create_email_template` grava templates no workspace ativo.
- `list_email_templates` lista apenas templates do workspace ativo.
- `get_email_template` retorna vazio para template de outro workspace.
- `create_email_template_version` recusa template fora do workspace ativo.
- `template_version_for_render` filtra por workspace ativo tanto por template
  quanto por versao.
- `render_email_template` audita no workspace ativo e preserva rodape de
  compliance.
- Teste de isolamento multi-workspace em `tests/test_email_templates.py`.
- Sequencias passaram a consumir templates no workspace ativo na Fase 20.
