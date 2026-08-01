# Guia de desenvolvimento

Este projeto deve manter um historico claro, rastreavel e compativel com as
praticas comuns da comunidade open source. O historico publico nao deve expor
ferramentas internas, agentes de IA ou automacoes usadas para apoiar a
implementacao.

## Issues, branches e PRs

- Toda fase relevante deve partir de uma issue ou documento de escopo.
- Branches devem usar nomes semanticos e neutros, sem prefixos ou sufixos de
  ferramenta, IA, agente ou fornecedor.
- Padroes recomendados:
  - `feature/<numero>-<slug>`
  - `fix/<slug>`
  - `docs/<slug>`
  - `refactor/<slug>`
  - `chore/<slug>`
- PRs devem explicar objetivo, mudancas, riscos, testes executados e proximos
  passos.
- PRs e commits nao devem usar coautoria automatica de agente ou ferramenta.

## Commits

- Commits devem seguir Conventional Commits:
  - `feat: ...`
  - `fix: ...`
  - `docs: ...`
  - `refactor: ...`
  - `test: ...`
  - `chore: ...`
- Cada commit deve representar uma unidade logica pequena.
- Mensagens de commit devem descrever o produto ou codigo alterado, nao a
  ferramenta usada para gerar a alteracao.

## Documentacao obrigatoria

Mudancas estruturais devem atualizar a documentacao no mesmo PR:

- arquitetura e decisoes relevantes;
- modelo de dados e migrations;
- contrato de API quando endpoints publicos mudarem;
- instrucoes de operacao local;
- riscos, limites e criterios de verificacao.

