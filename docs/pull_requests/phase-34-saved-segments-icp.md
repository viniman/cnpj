# PR local - Fase 34: Segmentos salvos e conversao para ICP

## Objetivo

Permitir que uma busca filtrada de empresas seja salva como segmento e
convertida em ICP estruturado para o fluxo SDR.

## Implementado

- [x] Documento `docs/SAVED_SEGMENT_ICP_SPEC.md`.
- [x] ADR sobre segmento como fotografia de filtros.
- [x] Servicos para criar/listar segmentos salvos.
- [x] Conversao de segmento para `icp_rules`.
- [x] Endpoints `GET/POST /api/saved-filters`.
- [x] Endpoint `POST /api/saved-filters/{id}/icp`.
- [x] UI na tela `Empresas` para salvar/aplicar/converter.
- [x] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saved_segments
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [x] Segmento salva filtros normalizados.
- [x] Segmento guarda contagem snapshot.
- [x] Segmentos sao isolados por workspace.
- [x] Segmento pode virar ICP.
- [x] ICP criado preserva `source_filters`.
- [x] UI permite salvar, aplicar e converter.

## Verificacao realizada

```text
python -m unittest tests.test_saved_segments
Ran 4 tests
OK

python -m unittest discover -s tests
Ran 101 tests
OK

node --check static\app.js
OK
```
