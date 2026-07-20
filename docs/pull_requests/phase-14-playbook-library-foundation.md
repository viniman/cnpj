# PR local - Fase 14: Playbook library foundation

Branch: `feature/14-playbook-library-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de playbooks reutilizaveis por workspace, com conteudo
estruturado de ICP, copy, cadencia, OKR e governanca, versionamento e aplicacao
explicita ao workspace interno.

## Implementado

- Especificacao da fase em `docs/PLAYBOOK_LIBRARY_SPEC.md`.
- ADR-016 definindo playbooks como referencias versionadas.
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
- Perfil default do workspace interno.
- Playbook default para outbound B2B local.
- Criacao de playbook com versao 1 ativa.
- Criacao de nova versao ativa, arquivando a anterior.
- Aplicacao explicita de playbook/versao ao workspace.
- Painel `Playbooks` no Command Center.
- Testes cobrindo default, criacao, versionamento, aplicacao e bootstrap
  idempotente.

## Checklist de aceite

- [x] Existe playbook default quando o banco nao tem playbooks.
- [x] Criar playbook gera versao 1 ativa.
- [x] Criar nova versao incrementa `version_number`.
- [x] Nova versao arquiva a ativa anterior.
- [x] Aplicar playbook registra `workspace_playbook_applications`.
- [x] `GET /api/playbooks` retorna biblioteca e aplicacao ativa.
- [x] UI do Command Center permite ver, criar, versionar e aplicar playbooks.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 54 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
defaults_before=1
created_playbook_id=2
created_active_version=1
created_version_id=3
created_version_number=2
active_application_id=1
active_playbook_name=Smoke Playbook 20260720015844
active_version=2
playbooks_after=2
```

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Aplicar playbook nesta fase nao sobrescreve ICP, sequencias, OKRs ou
  configuracoes do agente.
- Wizard completo de onboarding e comparacao multi-workspace ficam para fases
  futuras.
