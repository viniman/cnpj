# PR local - Fase 37: Historico e rollback de score

## Objetivo

Adicionar versionamento e rollback para configuracoes de score de e-mail e de
empresa por workspace.

## Implementado

- [x] Documento `docs/SCORING_CONFIG_VERSION_HISTORY_SPEC.md`.
- [x] ADR sobre versionamento de configuracoes de score.
- [x] Tabela `workspace_score_config_versions`.
- [x] Versao default automatica para score de e-mail e empresa.
- [x] Nova versao a cada atualizacao de configuracao.
- [x] Rollback criando nova versao ativa baseada no snapshot antigo.
- [x] Endpoints `GET /api/scoring/config-versions` e
  `POST /api/scoring/config-versions/{id}/rollback`.
- [x] UI local para listar historico e restaurar versao.
- [x] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_scoring_config_versions tests.test_workspace_scoring_config tests.test_workspace_company_score_config
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [x] Versao 1 e criada para defaults de e-mail e empresa.
- [x] Atualizacao de e-mail cria nova versao ativa.
- [x] Atualizacao de empresa cria nova versao ativa.
- [x] Rollback restaura snapshot antigo e cria nova versao.
- [x] Versoes ficam isoladas por workspace.
- [x] UI lista versoes e aciona rollback.

## Verificacao realizada

```text
python -m unittest tests.test_scoring_config_versions tests.test_workspace_scoring_config tests.test_workspace_company_score_config
Ran 12 tests
OK

python -m unittest discover -s tests
Ran 113 tests
OK

node --check static\app.js
OK
```
