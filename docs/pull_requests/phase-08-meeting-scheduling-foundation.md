# PR local - Fase 08: Meeting scheduling foundation

Branch: `feature/08-meeting-scheduling-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de reunioes e agenda operacional para transformar handoffs
humanos em proxima acao comercial registrada, sem integracao real de calendario
ou envio automatico.

## Implementado

- Especificacao da fase em `docs/MEETING_SCHEDULING_SPEC.md`.
- ADR-010 definindo que reunioes exigem decisao humana explicita.
- Tabela `meetings`.
- Servicos:
  - criar reuniao manual por `lead_id`
  - criar reuniao a partir de `handoff_id`
  - bloquear reuniao para lead em opt-out ou e-mail suprimido
  - resolver handoff quando reuniao e criada por handoff
  - listar reunioes com contexto de empresa/lead
  - atualizar status de reuniao
  - atualizar status do lead e conversoes do funil
  - registrar `agent_actions` e auditoria
- API:
  - `POST /api/handoffs/{id}/meeting`
  - `POST /api/meetings`
  - `GET /api/meetings`
  - `POST /api/meetings/{id}/status`
- UI:
  - controles de reuniao na aba `Respostas`
  - acao rapida `Reuniao` em handoff pendente
  - tabela de reunioes recentes
  - atualizacao de status de reuniao com nota

## Checklist de aceite

- [x] Criar reuniao por handoff pendente resolve o handoff e atualiza lead.
- [x] Criar reuniao bloqueia lead em opt-out ou e-mail suprimido.
- [x] Criar reuniao registra conversao `meeting_scheduled`.
- [x] Atualizar status registra `agent_actions` e atualiza lead.
- [x] API lista reunioes com contexto da empresa e do lead.
- [x] UI permite criar e revisar reunioes na aba `Respostas`.
- [x] Testes automatizados cobrem criacao, bloqueio e status.
- [ ] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 37 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Simule uma resposta de interesse em `Respostas`.
3. Clique em `Reuniao` no handoff pendente.
4. Preencha horario/link/nota e crie a reuniao por handoff.
5. Atualize a reuniao para `completed` ou `cancelled`.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Esta fase nao envia convite nem sincroniza calendario.
- Opt-out e supressao bloqueiam criacao de reuniao.
