# PR local - Fase 36: Score de empresa configuravel por workspace

## Objetivo

Permitir que cada workspace ajuste o score comercial de empresas sem alterar
codigo e sem sobrescrever o score base global.

## Implementado

- [x] Documento `docs/WORKSPACE_COMPANY_SCORE_CONFIG_SPEC.md`.
- [x] ADR sobre score de empresa por workspace.
- [x] Tabelas `workspace_company_score_configs` e `company_workspace_scores`.
- [x] Default idempotente por workspace.
- [x] Servicos para ler/atualizar configuracao.
- [x] Recalculo controlado por workspace.
- [x] Busca, detalhe e ICP usando score do workspace como overlay.
- [x] Endpoints `GET/POST /api/scoring/company-config` e
  `POST /api/scoring/company-rescore`.
- [x] UI local para visualizar, salvar e recalcular score de empresa.
- [x] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_company_score_config tests.test_scoring
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [x] Default e criado por workspace.
- [x] Config customizada altera score calculado do workspace.
- [x] Score base global da empresa nao e sobrescrito pelo overlay.
- [x] Customizacao nao vaza entre workspaces.
- [x] Busca, detalhe e ICP usam overlay quando existente.
- [x] UI permite salvar regras e recalcular lote controlado.

## Verificacao realizada

```text
python -m unittest tests.test_workspace_company_score_config tests.test_scoring
Ran 6 tests
OK

python -m unittest discover -s tests
Ran 109 tests
OK

node --check static\app.js
OK
```
