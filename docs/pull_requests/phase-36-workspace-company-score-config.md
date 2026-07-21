# PR local - Fase 36: Score de empresa configuravel por workspace

## Objetivo

Permitir que cada workspace ajuste o score comercial de empresas sem alterar
codigo e sem sobrescrever o score base global.

## Implementado

- [x] Documento `docs/WORKSPACE_COMPANY_SCORE_CONFIG_SPEC.md`.
- [ ] ADR sobre score de empresa por workspace.
- [ ] Tabelas `workspace_company_score_configs` e `company_workspace_scores`.
- [ ] Default idempotente por workspace.
- [ ] Servicos para ler/atualizar configuracao.
- [ ] Recalculo controlado por workspace.
- [ ] Busca, detalhe e ICP usando score do workspace como overlay.
- [ ] Endpoints `GET/POST /api/scoring/company-config` e
  `POST /api/scoring/company-rescore`.
- [ ] UI local para visualizar, salvar e recalcular score de empresa.
- [ ] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_workspace_company_score_config tests.test_scoring
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [ ] Default e criado por workspace.
- [ ] Config customizada altera score calculado do workspace.
- [ ] Score base global da empresa nao e sobrescrito pelo overlay.
- [ ] Customizacao nao vaza entre workspaces.
- [ ] Busca, detalhe e ICP usam overlay quando existente.
- [ ] UI permite salvar regras e recalcular lote controlado.

## Verificacao realizada

Pendente ate a implementacao.
