# PR - Fase 42: Decisões de arquitetura e próximas fases

Issue: https://github.com/viniman/cnpj/issues/3

## Contexto

Esta fase consolida as decisões arquiteturais tomadas antes de avançar para a
migração real para PostgreSQL, importação completa da Receita Federal, futuro
backend NestJS, frontend Next.js e separação entre super admin e produto
cliente.

## Mudanças

- Adicionado `docs/NEXT_ARCHITECTURE_LEDGER.md` como livro razão da arquitetura
  alvo, próximas fases e diferenciais futuros.
- Adicionado `docs/PHASE_HISTORY_INDEX.md` para preservar a navegação das fases
  01 a 42 mesmo sem PR remoto individual para as fases antigas.
- Adicionado `docs/DEVELOPMENT_GUIDELINES.md` com padrões de issues, branches,
  commits e PRs sem marca de ferramenta ou IA.
- Adicionado `docs/UI_INTERFACE_PRINCIPLES.md` com princípios de interface para
  produto cliente e super admin.
- Atualizado `docs/ARCHITECTURE.md` com a decisão de PostgreSQL central e
  schemas separados.
- Atualizado `docs/PRODUCT_ROADMAP.md` com decisões pós-fase 41, cadências,
  `llms.txt`, histórico mensal e diferenciais.
- Atualizado `docs/DECISIONS.md` com ADRs 044 a 047.
- Atualizado `README.md` apontando os documentos de direção.

## Decisões registradas

- PostgreSQL central com schemas `receita_staging`, `app`, `billing` e `audit`.
- Python permanece como motor de ETL e jobs da Receita.
- NestJS/Prisma será dono do backend de produto e migrations operacionais.
- Next.js será a interface premium de cliente e pode assumir super admin futuro.
- SQLite deve sair do fluxo principal após a migração para Postgres.
- Histórico mensal, sócios antigos e alertas de mudança são diferenciais
  centrais.
- "Sequências" deve migrar para "Cadências" no novo domínio.
- O histórico Git deve usar padrões semânticos da comunidade, sem coautoria ou
  nomes ligados a ferramentas internas/IA.
- Branches antigas de fase podem ser apagadas depois de confirmado que seus
  commits estão contidos em `main` e que a documentação histórica permanece no
  repositório.

## Verificação

- Documentação revisada por diff.
- Sem mudanças de runtime.
