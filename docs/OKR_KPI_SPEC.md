# Fase 12 - OKRs e KPIs ligados ao funil real

## Objetivo

Criar a fundacao de metas operacionais para o Command Center: objetivos,
key results e KPIs com formula explicita, sempre calculados a partir dos dados
reais do funil local.

Esta fase evita "numero magico". Todo KPI precisa declarar sua formula e o
resultado deve ser rastreavel ate tabelas existentes.

## Escopo

- Modelo de dados:
  - `kpi_definitions`
  - `objectives`
  - `key_results`
- API:
  - `GET /api/okrs`
  - `POST /api/okrs`
- KPIs default de outbound B2B:
  - leads ativos
  - envios simulados
  - respostas recebidas
  - handoffs pendentes
  - reunioes abertas
  - reunioes concluidas
  - conversoes registradas
- Um OKR default sintetico quando ainda nao existir objetivo salvo.
- UI na aba `Comando`:
  - painel de OKRs/KPIs
  - progresso por KR
  - formula explicita do KPI
  - origem/tabelas usadas

## Fora do escopo desta fase

- Comparacao multi-empresa.
- Edicao completa de OKRs pela UI.
- Periodos fiscais avancados.
- Alertas/notificacoes automaticas.
- Custo de IA.

## Decisao central

Key Results nao armazenam o valor atual como verdade. Eles apontam para um
`kpi_key`, e o valor atual e calculado no momento da leitura usando as tabelas
operacionais.

## API

### `GET /api/okrs`

Resposta:

```json
{
  "kpis": [],
  "objectives": [
    {
      "id": 1,
      "title": "Validar outbound B2B com operacao auditavel",
      "key_results": [
        {
          "title": "Gerar 20 respostas recebidas",
          "kpi_key": "replies_received",
          "current_value": 8,
          "target_value": 20,
          "progress": 40
        }
      ]
    }
  ]
}
```

### `POST /api/okrs`

Payload:

```json
{
  "title": "Validar ICP software",
  "period_start": "2026-07-01",
  "period_end": "2026-09-30",
  "key_results": [
    {"title": "10 reunioes concluidas", "kpi_key": "meetings_completed", "target_value": 10}
  ]
}
```

## Criterios de aceite

- KPIs retornam formula, valor atual, unidade e tabelas de origem.
- OKR default aparece mesmo sem objetivo salvo.
- Criar OKR salva objetivo e key results vinculados a `kpi_key` valido.
- Key result com KPI desconhecido e rejeitado.
- Progresso e calculado como `min(100, current / target * 100)`.
- UI do Command Center mostra objetivos, KRs, progresso e formula.
- Testes automatizados cobrem calculo de KPI, OKR default e criacao.
