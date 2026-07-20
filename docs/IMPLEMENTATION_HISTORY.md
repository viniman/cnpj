# Historico de Implementacao

Este arquivo registra as etapas realizadas no projeto para preservar contexto,
decisoes e criterios de verificacao.

## 2026-07-19 - Baseline do MVP local

Commit: `0d421d3 chore: establish local MVP baseline`

Estado registrado:

- Aplicacao local `Radar CNPJ Interno` em Python standard library + SQLite.
- Frontend estatico operacional em `static/`.
- Descoberta automatica da fonte oficial Receita/SERPRO via WebDAV.
- Consulta individual via BrasilAPI.
- Importacao de amostra CSV e parser limitado de ZIPs oficiais.
- Busca/filtros de empresas, detalhe com socios, listas, higiene de e-mail,
  supressao, exportacao CSV/XLSX e auditoria.
- Testes unitarios basicos passando.

Motivo do baseline:

- O diretorio ainda nao era um repositorio Git.
- A partir deste ponto, toda etapa relevante deve ter branch e commits
  atomicos seguindo Conventional Commits.

## Protocolo de trabalho

1. Criar branch `feature/<numero>-<slug>`.
2. Registrar docs ou decisao antes de implementar feature grande.
3. Fazer commits pequenos por unidade logica.
4. Rodar testes antes de encerrar a etapa.
5. Atualizar este historico com o que mudou e como verificar.

## 2026-07-19 - Roadmap integrado e scoring avancado de e-mail

Branch: `feature/01-product-roadmap-and-email-scoring`

Commits:

- `709e14d docs: define roadmap and email scoring plan`
- `b0ac29d feat: add advanced email scoring`

Implementado:

- Roadmap das novas camadas: growth/scoring, enriquecimento, envio
  responsavel, agente SDR, command center e SaaS.
- ADRs iniciais sobre MVP local, prioridade do scoring antes de envio e
  restricoes para envio real.
- Especificacao do scoring avancado de e-mail.
- Modulo `radar_cnpj/email_scoring.py` com algoritmo puro e versionado.
- Tabelas `email_classifications`, `known_shared_domains` e `email_score_log`.
- Servico para pontuar e-mails avulsos, por empresa ou por lista.
- Endpoint `POST /api/emails/score`.
- UI de Higiene com botao `Pontuar emails`.
- Testes cobrindo decisor, descartavel, match com socio e contato
  compartilhado entre CNPJs.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 11 tests
OK
```

## 2026-07-20 - Inicio da fase 02 de enriquecimento empresarial

Branch: `feature/02-company-enrichment-foundation`

Estado inicial:

- Fase 01 mesclada localmente no `master` por fast-forward.
- Nao ha remoto Git configurado; PRs sao registrados em `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 11 tests`, `OK`.

Meta da fase:

- Criar a fundacao de enriquecimento responsavel por HTML/URL explicita.
- Persistir sinais em tabela propria, sem sobrescrever dados oficiais.
- Respeitar `robots.txt`, cache e TTL.
- Expor API local e testes automatizados.

Documento principal:

- `docs/COMPANY_ENRICHMENT_SPEC.md`

Commits:

- `898775a docs: define company enrichment phase`
- `2f60285 feat: add company enrichment foundation`

Implementado:

- Tabelas `company_enrichment`, `scraping_jobs` e `scraping_cache`.
- Modulo `radar_cnpj/company_enrichment.py` para extrair e-mails, telefones,
  redes sociais, tecnologias e score de maturidade digital.
- Respeito a `robots.txt` antes de coleta externa por URL.
- Cache de HTML por URL com TTL configuravel.
- Servicos `enrich_company` e `get_company_enrichment`.
- Endpoints `POST /api/enrichment/company` e
  `GET /api/enrichment/company/{company_id}`.
- Aba `Enriquecimento` na UI local e botao `Enriquecer` no detalhe da empresa.
- Testes de parser, technology checker, score, cache e persistencia.

Como verificar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado nesta etapa:

```text
Ran 16 tests
OK
```

## 2026-07-20 - Inicio da fase 03 de CRM de experimento

Branch: `feature/03-email-experiment-foundation`

Estado inicial:

- Fase 02 mesclada localmente no `master`.
- Nao ha remoto Git configurado; PRs seguem registrados em
  `docs/pull_requests/`.
- Testes antes da nova fase: `Ran 16 tests`, `OK`.

Meta da fase:

- Criar leads a partir de listas qualificadas.
- Criar campanhas e variantes em modo simulado.
- Planejar envios simulados com trilhos duros de higiene, score e supressao.
- Registrar eventos e funil sem chamar provedor externo.

Documento principal:

- `docs/EMAIL_EXPERIMENT_SPEC.md`
