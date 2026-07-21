# PR local - Fase 35: Motor de score configuravel por workspace

## Objetivo

Permitir que cada workspace ajuste o dicionario de prefixos do scoring de
e-mail, mantendo defaults seguros e aplicacao no backend.

## Implementado

- [x] Documento `docs/WORKSPACE_SCORING_CONFIG_SPEC.md`.
- [x] ADR sobre scoring configuravel por workspace.
- [x] Tabela `workspace_scoring_configs`.
- [x] Default idempotente por workspace.
- [x] Servicos para ler/atualizar configuracao.
- [x] Aplicacao da configuracao em `score_email_record`.
- [x] Endpoints `GET/POST /api/scoring/config`.
- [x] UI local para visualizar e salvar regras.
- [x] Testes automatizados da fase.

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

- [x] Default e criado por workspace.
- [x] Prefixo customizado altera score persistido.
- [x] Customizacao nao vaza entre workspaces.
- [x] Algoritmo puro sem banco continua compativel.
- [x] UI permite salvar e recarregar configuracao ativa.

## Verificacao realizada

```text
python -m unittest tests.test_workspace_scoring_config tests.test_email_scoring
Ran 8 tests
OK

python -m unittest discover -s tests
Ran 105 tests
OK

node --check static\app.js
OK
```
