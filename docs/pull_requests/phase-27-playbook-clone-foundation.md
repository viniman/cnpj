# PR local - Fase 27: Playbook clone foundation

Branch: `feature/27-playbook-clone-foundation`

Base local: `master`

## Objetivo

Permitir reuso explicito e auditavel de playbooks entre workspaces, criando uma
copia independente no destino sem compartilhar estado nem aplicar
automaticamente configuracoes operacionais.

## Implementado

- Especificacao da fase em `docs/PLAYBOOK_CLONE_SPEC.md`.
- ADR-029 definindo reuso por clonagem auditavel.
- Servico `clone_playbook_to_workspace`.
- Endpoint `POST /api/playbooks/{id}/clone`.
- Clone por versao ativa ou `version_id` explicito.
- Auditoria na origem e no destino.
- Controle de clonagem no painel local de playbooks.
- Teste automatizado de isolamento multi-workspace.

## Checklist de aceite

- [x] Clonar playbook do workspace ativo cria novo playbook no destino.
- [x] O clone usa conteudo da versao ativa por padrao.
- [x] O clone pode usar uma versao especifica da origem.
- [x] Origem de outro workspace e recusada.
- [x] Destino inexistente ou igual ao workspace ativo e recusado.
- [x] Playbook clonado nao aparece no workspace de origem.
- [x] Playbook clonado aparece apenas ao trocar para o destino.
- [x] Auditoria registra a clonagem.
- [x] Testes automatizados cobrem isolamento e validacoes.

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
Ran 75 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- Clonar nao aplica o playbook no destino; a aplicacao continua sendo uma acao
  humana separada e auditavel.
