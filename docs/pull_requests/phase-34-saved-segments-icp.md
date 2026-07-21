# PR local - Fase 34: Segmentos salvos e conversao para ICP

## Objetivo

Permitir que uma busca filtrada de empresas seja salva como segmento e
convertida em ICP estruturado para o fluxo SDR.

## Implementado

- [ ] Documento `docs/SAVED_SEGMENT_ICP_SPEC.md`.
- [ ] ADR sobre segmento como fotografia de filtros.
- [ ] Servicos para criar/listar segmentos salvos.
- [ ] Conversao de segmento para `icp_rules`.
- [ ] Endpoints `GET/POST /api/saved-filters`.
- [ ] Endpoint `POST /api/saved-filters/{id}/icp`.
- [ ] UI na tela `Empresas` para salvar/aplicar/converter.
- [ ] Testes automatizados da fase.

## Como testar localmente

```powershell
$env:TEMP='D:\Projects\vagou\receita-federal-cnpj\.tmp-tests'
$env:TMP=$env:TEMP
python -m unittest tests.test_saved_segments
python -m unittest discover -s tests
node --check static\app.js
```

## Checklist de aceite

- [ ] Segmento salva filtros normalizados.
- [ ] Segmento guarda contagem snapshot.
- [ ] Segmentos sao isolados por workspace.
- [ ] Segmento pode virar ICP.
- [ ] ICP criado preserva `source_filters`.
- [ ] UI permite salvar, aplicar e converter.
