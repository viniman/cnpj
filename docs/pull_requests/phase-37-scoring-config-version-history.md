# PR local - Fase 37: Historico e rollback de score

## Objetivo

Adicionar versionamento e rollback para configuracoes de score de e-mail e de
empresa por workspace.

## Implementado

- [x] Documento `docs/SCORING_CONFIG_VERSION_HISTORY_SPEC.md`.
- [ ] ADR sobre versionamento de configuracoes de score.
- [ ] Tabela `workspace_score_config_versions`.
- [ ] Versao default automatica para score de e-mail e empresa.
- [ ] Nova versao a cada atualizacao de configuracao.
- [ ] Rollback criando nova versao ativa baseada no snapshot antigo.
- [ ] Endpoints `GET /api/scoring/config-versions` e
  `POST /api/scoring/config-versions/{id}/rollback`.
- [ ] UI local para listar historico e restaurar versao.
- [ ] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_scoring_config_versions tests.test_workspace_scoring_config tests.test_workspace_company_score_config
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [ ] Versao 1 e criada para defaults de e-mail e empresa.
- [ ] Atualizacao de e-mail cria nova versao ativa.
- [ ] Atualizacao de empresa cria nova versao ativa.
- [ ] Rollback restaura snapshot antigo e cria nova versao.
- [ ] Versoes ficam isoladas por workspace.
- [ ] UI lista versoes e aciona rollback.

## Verificacao realizada

Pendente ate a implementacao.
