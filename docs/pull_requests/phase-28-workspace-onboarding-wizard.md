# PR local - Fase 28: Workspace onboarding wizard

Branch: `feature/28-workspace-onboarding-wizard`

Base local: `master`

## Objetivo

Criar um wizard local que deixe uma nova empresa operacional rapidamente,
compondo workspace, perfil, playbook, ICP, template, sequencia, OKR e
configuracao default do agente sem quebrar auditoria ou aprovacao humana.

## Implementado

- Especificacao da fase em `docs/WORKSPACE_ONBOARDING_SPEC.md`.
- ADR-030 definindo onboarding como composicao de servicos existentes.
- Tabela `workspace_onboarding_runs`.
- Servico `run_workspace_onboarding`.
- Endpoint `POST /api/workspaces/onboarding`.
- Painel `Onboarding operacional` no Command Center.
- Testes automatizados cobrindo onboarding default e com playbook clonado.

## Checklist de aceite

- [x] Onboarding cria novo workspace e o torna ativo.
- [x] Perfil operacional recebe dados informados.
- [x] Playbook e aplicado ao workspace criado.
- [x] ICP inicial e criado no workspace novo.
- [x] Template inicial e criado com versao ativa.
- [x] Sequencia inicial usa o template criado e exige aprovacao humana.
- [x] OKR inicial e criado com KR rastreavel.
- [x] Reuso de playbook clonado e opcional e auditavel.
- [x] Testes automatizados provam que tudo fica no novo workspace.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_onboarding
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 77 tests
OK
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O drive `C:` do ambiente esta sem espaco livre; os testes completos devem
  usar `TEMP/TMP` em `D:` ate o ambiente ser limpo.
- O wizard nao cria leads, nao inscreve listas e nao envia e-mail; ele deixa a
  base operacional pronta para revisao humana.
