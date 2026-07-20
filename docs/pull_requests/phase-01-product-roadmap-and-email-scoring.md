# PR - Fase 01: Roadmap integrado e scoring avancado de e-mail

Branch: `feature/01-product-roadmap-and-email-scoring`

## Objetivo

Organizar os prompts mestres em um roadmap executavel e implementar a primeira
fatia funcional de alto impacto: scoring avancado de e-mail com explicacao,
persistencia e API.

## O que foi implementado

- Baseline Git do MVP local.
- Roadmap integrado das camadas futuras.
- ADRs iniciais.
- Especificacao de scoring avancado.
- Algoritmo `email-score-v1`.
- Tabelas:
  - `email_classifications`
  - `known_shared_domains`
  - `email_score_log`
- Endpoint `POST /api/emails/score`.
- UI de Higiene com botao `Pontuar emails`.
- Testes novos para regras e persistencia.

## Checklist

- [x] Branch dedicada criada.
- [x] Commits atomicos seguindo Conventional Commits.
- [x] Historico atualizado.
- [x] Documentacao de uso atualizada.
- [x] Testes automatizados passando.
- [x] Endpoint HTTP validado localmente.
- [ ] PR remoto aberto.
- [ ] Branch enviada para remoto.

## Como testar

```powershell
python -m unittest discover -s tests
```

Opcional, com o servidor rodando:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/emails/score" `
  -Body '{"emails":["ceo@empresa.com.br","contato@empresa.com.br","teste@mailinator.com"]}' `
  -ContentType "application/json"
```

## Evidencias locais

- `python -m unittest discover -s tests`: 11 testes, OK.
- `GET /api/health`: `ok=True`.
- `POST /api/emails/score`: retorna scores para decisor, generico e descartavel.

## Observacao

Ainda nao existe remoto Git configurado neste workspace. Assim que um remoto for
adicionado, fazer:

```powershell
git push -u origin feature/01-product-roadmap-and-email-scoring
```

e abrir PR usando este arquivo como descricao.

