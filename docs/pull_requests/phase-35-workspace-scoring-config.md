# PR local - Fase 35: Motor de score configuravel por workspace

## Objetivo

Permitir que cada workspace ajuste o dicionario de prefixos do scoring de
e-mail, mantendo defaults seguros e aplicacao no backend.

## Implementado

- [ ] Documento `docs/WORKSPACE_SCORING_CONFIG_SPEC.md`.
- [ ] ADR sobre scoring configuravel por workspace.
- [ ] Tabela `workspace_scoring_configs`.
- [ ] Default idempotente por workspace.
- [ ] Servicos para ler/atualizar configuracao.
- [ ] Aplicacao da configuracao em `score_email_record`.
- [ ] Endpoints `GET/POST /api/scoring/config`.
- [ ] UI local para visualizar e salvar regras.
- [ ] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_scoring_config
python -m unittest tests.test_email_scoring
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [ ] Default e criado por workspace.
- [ ] Prefixo customizado altera score persistido.
- [ ] Customizacao nao vaza entre workspaces.
- [ ] Algoritmo puro sem banco continua compativel.
- [ ] UI permite salvar e recarregar configuracao ativa.
