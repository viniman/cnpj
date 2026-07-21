# PR local - Fase 38: Diff visual de score

## Objetivo

Adicionar comparacao legivel entre a configuracao ativa de score do workspace e
uma versao historica, permitindo revisar o impacto antes de rollback.

## Implementado

- [x] Documento `docs/SCORING_CONFIG_DIFF_SPEC.md`.
- [x] ADR sobre diff por snapshots versionados.
- [x] Comparador deterministico de JSON para configuracoes de score.
- [x] Endpoint `GET /api/scoring/config-versions/{id}/diff`.
- [x] UI local com botao `Diff`, resumo e tabela de campos alterados.
- [x] Confirmacao de rollback mostrando quantidade de campos que mudarao.
- [x] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_scoring_config_versions tests.test_server_routes
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [x] Diff de e-mail identifica mudanca em regra de prefixo.
- [x] Diff de empresa identifica mudanca em regra comercial.
- [x] Versoes de outro workspace nao podem ser comparadas pelo workspace ativo.
- [x] UI mostra resumo e campos alterados antes do rollback.
- [x] Rollback continua criando nova versao ativa pelo contrato da fase 37.

## Verificacao realizada

```text
python -m unittest tests.test_scoring_config_versions tests.test_server_routes
Ran 8 tests
OK

python -m unittest discover -s tests
Ran 116 tests
OK

node --check static\app.js
OK
```
