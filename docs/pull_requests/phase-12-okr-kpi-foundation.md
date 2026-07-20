# PR local - Fase 12: OKR/KPI foundation

Branch: `feature/12-okr-kpi-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de OKRs e KPIs do Command Center, com progresso calculado a
partir das tabelas reais do funil e formula explicita para cada KPI.

## Implementado

- Especificacao da fase em `docs/OKR_KPI_SPEC.md`.
- ADR-014 definindo Key Results vinculados a KPIs calculados.
- Modelo de dados:
  - `kpi_definitions`
  - `objectives`
  - `key_results`
- API:
  - `GET /api/okrs`
  - `POST /api/okrs`
- Catalogo default com 7 KPIs:
  - leads ativos
  - envios simulados
  - respostas recebidas
  - handoffs pendentes
  - reunioes abertas
  - reunioes concluidas
  - conversoes registradas
- OKR default sintetico quando ainda nao ha objetivo salvo.
- Criacao de objetivo com validacao de `kpi_key` e meta maior que zero.
- Painel `OKRs e KPIs` na aba `Comando`.
- Testes cobrindo calculo, OKR default, criacao e validacao.

## Checklist de aceite

- [x] KPIs retornam formula, valor atual, unidade e tabelas de origem.
- [x] OKR default aparece sem objetivo salvo.
- [x] Criar OKR salva objetivo e KRs vinculados a `kpi_key` valido.
- [x] KPI desconhecido e rejeitado.
- [x] Progresso e calculado por valor atual / meta.
- [x] UI do Command Center mostra objetivos, KRs, progresso e formula.
- [x] Testes automatizados cobrem calculo de KPI, OKR default e criacao.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 46 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
kpis=7
default_objective_before=default
created_objective_id=1
created_kr_kpi=meetings_completed
created_kr_progress=100
meetings_completed_value=4
objectives_after=1
first_saved_objective=1
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O valor atual dos Key Results e calculado no momento da leitura.
- Edicao completa de OKRs pela UI fica fora desta fase.
