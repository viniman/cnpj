# PR - Fase 42: Decisoes de arquitetura e proximas fases

Issue: https://github.com/viniman/cnpj/issues/3

## Contexto

Esta fase consolida as decisoes arquiteturais tomadas antes de avancar para a
migracao real para PostgreSQL, importacao completa da Receita Federal, futuro
backend NestJS, frontend Next.js e separacao entre super admin e produto
cliente.

## Mudancas

- Adicionado `docs/NEXT_ARCHITECTURE_LEDGER.md` como livro razao da arquitetura
  alvo, proximas fases e diferenciais futuros.
- Adicionado `docs/PHASE_HISTORY_INDEX.md` para preservar a navegacao das fases
  01 a 42 mesmo sem PR remoto individual para as fases antigas.
- Adicionado `docs/DEVELOPMENT_GUIDELINES.md` com padroes de issues, branches,
  commits e PRs sem marca de ferramenta ou IA.
- Adicionado `docs/UI_INTERFACE_PRINCIPLES.md` com principios de interface para
  produto cliente e super admin.
- Atualizado `docs/ARCHITECTURE.md` com a decisao de PostgreSQL central e
  schemas separados.
- Atualizado `docs/PRODUCT_ROADMAP.md` com decisoes pos-fase 41, cadencias,
  `llms.txt`, historico mensal e diferenciais.
- Atualizado `docs/DECISIONS.md` com ADRs 044 a 047.
- Atualizado `README.md` apontando os documentos de direcao.

## Decisoes registradas

- PostgreSQL central com schemas `receita_staging`, `app`, `billing` e `audit`.
- Python permanece como motor de ETL e jobs da Receita.
- NestJS/Prisma sera dono do backend de produto e migrations operacionais.
- Next.js sera a interface premium de cliente e pode assumir super admin futuro.
- SQLite deve sair do fluxo principal apos a migracao para Postgres.
- Historico mensal, socios antigos e alertas de mudanca sao diferenciais
  centrais.
- "Sequencias" deve migrar para "Cadencias" no novo dominio.
- O historico Git deve usar padroes semanticos da comunidade, sem coautoria ou
  nomes ligados a ferramentas internas/IA.
- Branches antigas de fase podem ser apagadas depois de confirmado que seus
  commits estao contidos em `main` e que a documentacao historica permanece no
  repositorio.

## Verificacao

- Documentacao revisada por diff.
- Sem mudancas de runtime.
