# Fase 13 - Governanca do agente e custo de IA

## Objetivo

Criar a fundacao de governanca do agente SDR: versionamento de configuracao,
simulacao em staging antes de ativar mudancas, rollback por ativacao de versao
anterior e rastreio de custo estimado por acao.

Esta fase ainda nao chama modelo externo. Ela cria os trilhos de produto e
auditoria para que chamadas reais de IA possam ser ligadas depois sem virar
caixa-preta.

## Escopo

- Modelo de dados:
  - `agent_config_versions`
  - `agent_simulations`
  - `agent_cost_log`
- API:
  - `GET /api/agent-governance`
  - `POST /api/agent-governance/configs`
  - `POST /api/agent-governance/configs/{id}/activate`
  - `POST /api/agent-governance/simulations`
  - `POST /api/agent-governance/costs`
- Configuracao default ativa para o agente SDR.
- Criacao de novas versoes em `staging`.
- Ativacao explicita de versao, arquivando a ativa anterior.
- Simulacao deterministica local, sem chamada real de LLM.
- Registro de custo estimado por operacao/modelo/lead.
- Painel no Command Center com:
  - versao ativa
  - historico de versoes
  - simulacoes recentes
  - resumo de custo

## Fora do escopo desta fase

- Chamada real a OpenAI/Anthropic.
- Comparacao automatica entre prompts.
- Rollback com diff visual.
- Permissoes/RBAC reais.
- Aplicar `agent_config_version_id` retroativamente a `agent_actions`.

## Decisao central

Toda mudanca de comportamento do agente nasce como versao em `staging`. Ela so
entra em producao quando uma acao explicita ativa a versao. O custo de IA fica
em tabela propria, agregavel por lead, modelo e versao de configuracao.

## API

### `GET /api/agent-governance`

Resposta:

```json
{
  "active_config": {},
  "versions": [],
  "simulations": [],
  "cost_summary": {
    "total_calls": 3,
    "total_tokens": 1200,
    "estimated_cost": 0.024
  }
}
```

### `POST /api/agent-governance/configs`

Payload:

```json
{
  "name": "SDR conservador",
  "model_name": "gpt-5-mini",
  "prompt_text": "Tom direto, B2B, sem promessas inventadas.",
  "rules": {"requires_human_approval": true}
}
```

### `POST /api/agent-governance/configs/{id}/activate`

Ativa uma versao existente e arquiva a versao ativa anterior.

### `POST /api/agent-governance/simulations`

Payload:

```json
{
  "config_version_id": 2,
  "lead_id": 10,
  "scenario": "first_contact"
}
```

### `POST /api/agent-governance/costs`

Payload:

```json
{
  "config_version_id": 2,
  "lead_id": 10,
  "operation": "classify_reply",
  "model_name": "gpt-5-mini",
  "prompt_tokens": 500,
  "completion_tokens": 120,
  "estimated_cost": 0.012
}
```

## Criterios de aceite

- Existe uma configuracao default ativa quando o banco nao tem versoes.
- Criar config gera nova versao em `staging`.
- Ativar config muda a versao ativa e arquiva a ativa anterior.
- Simulacao registra resultado com `config_version_id` e opcionalmente `lead_id`.
- Custo registra tokens, custo estimado e alimenta resumo agregado.
- UI do Command Center mostra versao ativa, historico, simulacoes e custo.
- Testes automatizados cobrem default, criacao, ativacao, simulacao e custo.
