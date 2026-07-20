# PR local - Fase 03: Email experiment foundation

Branch: `feature/03-email-experiment-foundation`

Base local: `master`

## Objetivo

Criar a fundacao do CRM de experimento comercial em modo simulado, permitindo
testar listas, campanhas e funil sem enviar e-mail real.

## Implementado

- Especificacao da fase em `docs/EMAIL_EXPERIMENT_SPEC.md`.
- ADR-005 definindo campanhas apenas simuladas no MVP local.
- Tabelas:
  - `leads`
  - `campaigns`
  - `campaign_variants`
  - `sends`
  - `events`
  - `conversions`
  - `throttle_config`
  - `pause_events`
- Servicos:
  - criar leads a partir de lista
  - criar campanha simulada
  - simular campanha
  - registrar eventos de funil
  - calcular funil agregado
- API:
  - `POST /api/experiments/leads/from-list`
  - `GET /api/experiments/leads`
  - `POST /api/experiments/campaigns`
  - `GET /api/experiments/campaigns`
  - `GET /api/experiments/campaigns/{id}`
  - `POST /api/experiments/campaigns/{id}/simulate`
  - `POST /api/experiments/events`
- UI:
  - nova aba `Experimentos`
  - criacao de leads por lista
  - criacao de campanha simulada
  - simulacao de campanha
  - registro manual de evento
  - tabelas de campanhas e leads

## Checklist de aceite

- [x] Leads sao criados a partir de lista sem duplicar empresa/e-mail.
- [x] Leads sem qualidade minima sao bloqueados com motivo claro.
- [x] E-mail em supressao nao gera `simulated_sent`.
- [x] Campanha criada sempre nasce em `mode = simulated`.
- [x] Simulacao cria `sends` e `events`, mas nao chama provedor externo.
- [x] Funil mostra enviados, cliques, respostas, conversoes, bounces,
  complaints e bloqueios.
- [x] Bounce/complaint simulado adiciona supressao.
- [x] Testes automatizados cobrem os guardrails centrais.

## Como testar localmente

```powershell
python -m unittest discover -s tests
```

Resultado esperado:

```text
Ran 19 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Carregue a amostra.
3. Crie uma lista e adicione empresas.
4. Abra `Experimentos`.
5. Crie leads da lista.
6. Crie uma campanha simulada.
7. Clique em `Simular`.
8. Registre evento manual usando o ID de um envio.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O provider permanece `simulated`.
- AWS SES, SNS, QStash e DNS real seguem fora desta fase por seguranca.
