# PR local - Fase 02: Company enrichment foundation

Branch: `feature/02-company-enrichment-foundation`

Base local: `master`

## Objetivo

Criar a fundacao de enriquecimento responsavel de empresas, mantendo sinais de
site separados do dado oficial da Receita.

## Implementado

- Especificacao da fase em `docs/COMPANY_ENRICHMENT_SPEC.md`.
- ADR-004 sobre separacao entre dado oficial e enriquecimento.
- Tabelas:
  - `company_enrichment`
  - `scraping_jobs`
  - `scraping_cache`
- Parser de HTML para:
  - e-mails publicados
  - telefones/WhatsApp
  - links sociais
  - tecnologias do site
- Score explicavel de maturidade digital.
- API:
  - `POST /api/enrichment/company`
  - `GET /api/enrichment/company/{company_id}`
- UI:
  - nova aba `Enriquecimento`
  - botao `Enriquecer` no detalhe da empresa
- Testes automatizados cobrindo parser, score, cache e persistencia.

## Checklist de aceite

- [x] Dado HTML de teste, parser extrai e-mails, telefones, redes sociais e tecnologias.
- [x] API persiste enriquecimento em `company_enrichment`.
- [x] URL externa passa por verificacao de `robots.txt`.
- [x] Cache evita nova requisicao quando a URL ainda esta dentro do TTL.
- [x] Resultado mostra origem, timestamp, score e explicacao.
- [x] Testes automatizados cobrem os principais cenarios da fase.

## Como testar localmente

```powershell
python -m unittest discover -s tests
```

Resultado esperado:

```text
Ran 16 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Carregue a amostra.
3. Abra uma empresa e clique em `Enriquecer`.
4. Cole um HTML simples com e-mail, telefone, link social e script de tecnologia.
5. Clique em `Enriquecer empresa`.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- Descoberta automatica de dominio oficial ficou fora desta fase; ela exige
  validacao de identidade do site candidato antes de vincular ao CNPJ.
