# PR local - Fase 06: ICP prioritization foundation

Branch: `feature/06-icp-prioritization-foundation`

Base local: `master`

## Objetivo

Adicionar ICP estruturado e fila SDR priorizada para que o agente futuro so
opere sobre leads que passem por filtros objetivos de fit e compliance.

## Implementado

- Especificacao da fase em `docs/ICP_PRIORITIZATION_SPEC.md`.
- ADR-008 definindo ICP estruturado como limite do agente.
- Tabelas:
  - `icp_rules`
  - `lead_priority_queue`
- Servicos:
  - criar/listar/buscar ICP
  - normalizar criterios estruturados
  - avaliar empresas/leads contra ICP
  - priorizar lista ou base inteira
  - listar fila SDR
  - aceitar/rejeitar sugestoes
- API:
  - `POST /api/icp-rules`
  - `GET /api/icp-rules`
  - `GET /api/icp-rules/{id}`
  - `POST /api/icp-rules/{id}/prioritize`
  - `GET /api/priority-queue`
  - `POST /api/priority-queue/{id}/accept`
  - `POST /api/priority-queue/{id}/reject`
- UI:
  - nova aba `ICP SDR`
  - formulario de ICP estruturado
  - seletor de lista opcional
  - tabela de regras ICP
  - tabela de fila SDR priorizada
  - aceite/rejeicao com nota

## Checklist de aceite

- [x] Regra ICP persiste criterios estruturados.
- [x] Priorizacao retorna apenas empresas/leads que passam no ICP.
- [x] E-mail suprimido nao entra na fila quando supressao esta ativa.
- [x] E-mail abaixo do score minimo nao entra na fila.
- [x] Sugestao mostra score, fit e motivos.
- [x] Aceitar/rejeitar sugestao muda status.
- [x] Priorizacao e decisoes registram `agent_actions`.
- [x] Testes automatizados cobrem fit, bloqueio e decisao.
- [ ] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
```

Resultado esperado:

```text
Ran 30 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Carregue a amostra.
3. Crie uma lista com empresas de software ou servicos.
4. Abra `ICP SDR`.
5. Crie um ICP por UF/CNAE/score.
6. Clique em `Priorizar`.
7. Aceite ou rejeite uma sugestao da fila.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- A fila SDR nao envia e-mail nem inscreve automaticamente em sequencia.
- Esta fase reduz risco de drift do agente: o ICP e regra de backend.
