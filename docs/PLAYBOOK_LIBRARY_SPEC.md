# Fase 14 - Biblioteca de playbooks reutilizaveis

## Objetivo

Criar a fundacao de playbooks reutilizaveis por workspace. Um playbook e um
pacote versionado que combina ICP, tom de copy, cadencia, metas e regras de
governanca para iniciar uma operacao outbound sem reconfigurar tudo do zero.

Esta fase continua local e interna. Ela nao cria marketplace publico nem cobra
creditos; o foco e deixar a plataforma capaz de reaplicar aprendizados entre
empresas suas de forma explicita e auditavel.

## Escopo

- Modelo de dados:
  - `company_profiles`
  - `playbooks`
  - `playbook_versions`
  - `workspace_playbook_applications`
- API:
  - `GET /api/playbooks`
  - `POST /api/playbooks`
  - `POST /api/playbooks/{id}/versions`
  - `POST /api/playbooks/{id}/apply`
- Playbooks default para outbound B2B local.
- Versionamento de conteudo estruturado do playbook.
- Aplicacao explicita do playbook ao workspace interno.
- Painel no Command Center com:
  - playbook ativo do workspace
  - biblioteca de playbooks
  - criacao de playbook
  - criacao de nova versao
  - acao de aplicar playbook

## Fora do escopo desta fase

- Wizard completo de onboarding multi-etapa.
- Copia entre varios workspaces reais.
- RBAC de aplicacao de playbook.
- Diff visual entre versoes.
- Aplicacao automatica que altere ICP, cadencia ou OKR ja existentes sem
  revisao humana.

## Decisao central

Aplicar um playbook nao apaga nem sobrescreve configuracoes operacionais
existentes. Nesta fase, a aplicacao grava um registro auditavel e marca o
playbook/versao como referencia ativa do workspace. Fases futuras podem usar
essa referencia para preencher formularios de ICP, templates, cadencias e
OKRs, sempre como acao explicita.

## Estrutura de conteudo

Cada `playbook_version` guarda `content_json` com chaves estruturadas:

```json
{
  "icp": {
    "states": ["SP"],
    "target_cnaes": ["620"],
    "min_email_score": 30
  },
  "copy": {
    "tone": "direto, B2B, consultivo",
    "first_touch_angle": "ganho operacional claro"
  },
  "cadence": {
    "steps": [
      {"name": "Primeiro contato", "wait_days": 0},
      {"name": "Follow-up curto", "wait_days": 3}
    ]
  },
  "okr": {
    "objective": "Validar nicho outbound",
    "key_results": [
      {"kpi_key": "replies_received", "target_value": 10}
    ]
  },
  "governance": {
    "requires_human_approval": true
  }
}
```

## API

### `GET /api/playbooks`

Resposta:

```json
{
  "active_application": {},
  "playbooks": []
}
```

### `POST /api/playbooks`

Payload:

```json
{
  "name": "Outbound B2B Servicos Locais",
  "description": "Playbook inicial para nichos regionais",
  "content": {}
}
```

Cria o playbook e a primeira versao ativa.

### `POST /api/playbooks/{id}/versions`

Payload:

```json
{
  "description": "Ajuste para lead com maior maturidade digital",
  "content": {}
}
```

Cria uma nova versao ativa do playbook e arquiva a ativa anterior.

### `POST /api/playbooks/{id}/apply`

Payload:

```json
{
  "version_id": 2,
  "note": "Aplicado para testar na Vagou"
}
```

Grava a aplicacao explicita no workspace atual.

## Criterios de aceite

- Existe ao menos um playbook default quando o banco esta vazio.
- Criar playbook gera versao 1 ativa.
- Criar nova versao incrementa `version_number` e torna a versao ativa.
- Aplicar playbook registra `workspace_playbook_applications` com `version_id`.
- `GET /api/playbooks` retorna biblioteca e aplicacao ativa.
- UI do Command Center permite ver, criar, versionar e aplicar playbooks.
- Testes automatizados cobrem default, criacao, versionamento e aplicacao.
