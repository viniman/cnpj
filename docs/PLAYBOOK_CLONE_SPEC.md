# Fase 27 - Clonagem auditavel de playbooks entre workspaces

## Objetivo

Permitir reutilizar um playbook que funcionou em uma empresa interna como ponto
de partida para outra empresa, sem compartilhar estado implicitamente. A copia
deve criar um novo playbook no workspace de destino, com versao inicial propria
e auditoria clara.

## Escopo

- Criar servico `clone_playbook_to_workspace`.
- Clonar a versao ativa, ou uma versao informada, para outro workspace.
- Validar que o playbook de origem pertence ao workspace ativo.
- Validar que o workspace de destino existe e e diferente do workspace ativo.
- Permitir renomear e ajustar descricao no ato de clonagem.
- Criar novo playbook e versao 1 no destino, sem aplicar automaticamente.
- Auditar a acao no workspace de origem e no destino.
- Expor endpoint local para clonagem.
- Adicionar controle simples na UI de playbooks.

## Fora do escopo desta fase

- Mesclar alteracoes entre clones.
- Aplicar automaticamente ICP, templates, sequencias, OKRs ou configuracoes.
- Marketplace global de playbooks.
- Permissoes/RBAC para restringir quem pode clonar.

## Decisao central

Reuso entre empresas deve ser copia auditavel, nao referencia compartilhada. O
workspace de destino recebe um novo playbook independente, preservando a origem
em metadados e deixando qualquer aplicacao operacional para acao posterior.

## Implementado nesta fase

- `clone_playbook_to_workspace` clona playbook do workspace ativo para destino.
- Clone usa versao ativa por padrao ou `version_id` explicito.
- Destino recebe default de playbook antes do clone quando ainda nao tinha
  biblioteca inicial.
- Novo playbook no destino nasce com `source = cloned` e versao 1 ativa.
- Endpoint `POST /api/playbooks/{id}/clone`.
- Painel local de playbooks ganhou seletor de workspace destino e campos de
  nome/descricao do clone.
- Auditoria registra `clone_playbook_to_workspace` na origem e
  `receive_cloned_playbook` no destino.
- Teste multi-workspace cobre clonagem, recusas, isolamento e auditoria.

## Criterios de aceite

- Clonar playbook do workspace ativo cria novo playbook no destino.
- O clone usa conteudo da versao ativa por padrao.
- O clone pode usar uma versao especifica da origem.
- Origem de outro workspace e recusada.
- Destino inexistente ou igual ao workspace ativo e recusado.
- Playbook clonado nao aparece no workspace de origem.
- Playbook clonado aparece apenas ao trocar para o destino.
- Auditoria registra a clonagem.
- Testes automatizados cobrem isolamento e validacoes.
