# PR local - Fase 10: Command Center action inbox

Branch: `feature/10-command-center-action-inbox`

Base local: `master`

## Objetivo

Tornar a inbox do Command Center acionavel, permitindo decisoes humanas sem
sair da aba `Comando`, mas delegando cada acao para o servico de origem.

## Implementado

- Especificacao da fase em `docs/COMMAND_ACTION_INBOX_SPEC.md`.
- ADR-012 definindo roteamento de acoes para servicos de origem.
- API:
  - `POST /api/command-center/actions`
- Acoes suportadas:
  - `approval`: `approve`, `reject`
  - `handoff`: `resolve`, `dismiss`
  - `meeting`: `complete`, `cancel`, `no_show`
- Payload de inbox agora inclui `actions` por item.
- UI:
  - nota de decisao na aba `Comando`
  - botoes de acao por item da inbox
  - re-renderizacao pelo snapshot `command_center` retornado pela API
- Testes cobrindo:
  - aprovar `approval`
  - decidir `handoff`
  - concluir `meeting`
  - rejeitar decisao invalida

## Checklist de aceite

- [x] Aprovar `approval` pela inbox executa a regra de sequencia.
- [x] Rejeitar combinacao invalida falha no backend.
- [x] Resolver `handoff` pela inbox registra decisao.
- [x] Concluir `meeting` pela inbox atualiza lead e reuniao.
- [x] API retorna snapshot atualizado do Command Center.
- [x] UI atualiza metrics/inbox/Kanban/feed apos decisao.
- [x] Testes automatizados cobrem as tres familias de item.
- [x] Smoke test HTTP final executado apos reiniciar servidor.

## Como testar localmente

```powershell
python -m unittest discover -s tests
node --check static\app.js
```

Resultado esperado:

```text
Ran 41 tests
OK
```

Smoke HTTP final executado em `2026-07-20`:

```text
health=True
list_id=15
company_id=11
lead_id=23
approvals_created=1
approval_id=6
approval_status=approved
handoff_id=6
handoff_status=resolved
meeting_id=4
meeting_status=completed
snapshot_inbox_items=5
final_inbox_items=5
kanban_columns=7
activity_items=36
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Gere ao menos uma aprovacao, handoff ou reuniao aberta.
3. Abra `Comando`.
4. Preencha a nota e execute uma acao na inbox.
5. Confirme que metricas, inbox, Kanban e feed foram atualizados.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Criacao de reuniao por handoff continua na aba `Respostas`.
- O endpoint nao aceita decisoes fora da lista permitida por `source_type`.
