# PR local - Fase 05: Sequence supervision foundation

Branch: `feature/05-sequence-supervision-foundation`

Base local: `master`

## Objetivo

Criar a primeira camada de cadencias semi-supervisionadas: o sistema prepara
passos de outbound a partir de templates e listas elegiveis, mas exige decisao
humana antes de qualquer execucao simulada.

## Implementado

- Especificacao da fase em `docs/SEQUENCE_SUPERVISION_SPEC.md`.
- ADR-007 definindo cadencias semi-supervisionadas antes de autonomia.
- Tabelas:
  - `sequences`
  - `sequence_steps`
  - `lead_journey`
  - `approval_queue`
  - `agent_actions`
- Servicos:
  - criar e listar sequencias
  - inscrever lista em sequencia
  - criar aprovacao do primeiro passo
  - aprovar ou rejeitar passo
  - preparar proximo passo de uma jornada
  - listar jornadas, aprovacoes e acoes do agente
- API:
  - `POST /api/sequences`
  - `GET /api/sequences`
  - `GET /api/sequences/{id}`
  - `POST /api/sequences/{id}/enroll`
  - `GET /api/sequences/journeys`
  - `POST /api/sequences/journeys/{id}/prepare-next`
  - `GET /api/approvals`
  - `POST /api/approvals/{id}/approve`
  - `POST /api/approvals/{id}/reject`
  - `GET /api/agent-actions`
- UI:
  - nova aba `Sequencias`
  - construtor de cadencia com ate dois passos no MVP
  - inscricao de lista em sequencia
  - fila de aprovacao humana com preview de assunto/corpo
  - decisao com nota
  - tabela de jornadas
  - log de acoes registradas

## Checklist de aceite

- [x] Sequencia exige pelo menos um passo com template ativo.
- [x] Inscricao cria jornadas apenas para leads elegiveis.
- [x] Cada jornada inscrita gera aprovacao pendente antes de envio.
- [x] Aprovacao cria envio simulado e evento `sent`.
- [x] Rejeicao nao cria envio.
- [x] Jornada com proximo passo fica em espera e pode preparar nova aprovacao.
- [x] Toda decisao relevante registra `agent_actions`.
- [x] Testes automatizados cobrem inscricao, aprovacao, rejeicao e proximo passo.
- [ ] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
```

Resultado esperado:

```text
Ran 27 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Carregue a amostra.
3. Crie uma lista com uma empresa elegivel.
4. Crie templates de primeiro contato e follow-up.
5. Abra `Sequencias`, crie uma cadencia e inscreva a lista.
6. Revise a aprovacao pendente e aprove.
7. Prepare o proximo passo quando a jornada ficar em espera.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Esta fase ainda opera em modo `simulated`.
- Autonomia real de SDR continua bloqueada ate ICP estruturado, resposta
  recebida, opt-out automatico e limites de envio real estarem implementados.
