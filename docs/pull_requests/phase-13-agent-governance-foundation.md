# PR local - Fase 13: Agent governance foundation

Branch: `feature/13-agent-governance-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de governanca do agente SDR: configuracoes versionadas,
staging antes de ativacao, simulacoes locais e custo estimado de IA visivel no
Command Center.

## Implementado

- Especificacao da fase em `docs/AGENT_GOVERNANCE_SPEC.md`.
- ADR-015 definindo staging antes de ativacao.
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
- Criacao de novas versoes como `staging`.
- Ativacao explicita de versao, arquivando a ativa anterior.
- Simulacao local deterministica sem envio e sem chamada real de LLM.
- Registro de custo estimado por operacao, modelo, lead e versao.
- Painel `Governanca do agente` na aba `Comando`.
- Testes cobrindo default, criacao, ativacao, simulacao e custo agregado.

## Checklist de aceite

- [x] Existe uma configuracao default ativa quando nao ha versoes.
- [x] Criar config gera uma nova versao em `staging`.
- [x] Ativar config arquiva a versao ativa anterior.
- [x] Simulacao registra `config_version_id`, cenario e contexto opcional de lead.
- [x] Custo registra tokens, custo estimado e alimenta resumo agregado.
- [x] UI do Command Center mostra versao ativa, historico, simulacoes e custo.
- [x] Testes automatizados cobrem os caminhos principais.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 50 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
active_before=1
created_config_id=3
created_version=3
created_status=staging
activated_status=active
active_after=3
simulation_id=2
simulation_decision=requires_human_review
cost_id=2
total_calls=2
total_tokens=1240
estimated_cost=0.024
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Esta fase nao chama OpenAI, Anthropic ou outro provedor externo.
- Rollback visual e comparacao automatica entre prompts ficam para fase futura.
