# Guia de desenvolvimento

Este projeto deve manter um histórico claro, rastreável e compatível com as
práticas comuns da comunidade open source. O histórico público não deve expor
ferramentas internas, agentes de IA ou automações usadas para apoiar a
implementação.

## Issues, branches e PRs

- Toda fase relevante deve partir de uma issue ou documento de escopo.
- Branches devem usar nomes semânticos e neutros, sem prefixos ou sufixos de
  ferramenta, IA, agente ou fornecedor.
- Padrões recomendados:
  - `feature/<numero>-<slug>`
  - `fix/<slug>`
  - `docs/<slug>`
  - `refactor/<slug>`
  - `chore/<slug>`
- PRs devem explicar objetivo, mudanças, riscos, testes executados e próximos
  passos.
- PRs e commits não devem usar coautoria automática de agente ou ferramenta.

## Commits

- Commits devem seguir Conventional Commits:
  - `feat: ...`
  - `fix: ...`
  - `docs: ...`
  - `refactor: ...`
  - `test: ...`
  - `chore: ...`
- Cada commit deve representar uma unidade lógica pequena.
- Mensagens de commit devem descrever o produto ou código alterado, não a
  ferramenta usada para gerar a alteração.

## Português e acentuação

- Documentos em português devem usar acentuação correta, incluindo ç/Ç,
  caracteres acentuados e concordância gramatical.
- Evite substituir palavras acentuadas por versões sem acento apenas por
  conveniência técnica.
- Antes de abrir PR de documentação, revise títulos, listas e descrições para
  corrigir erros como "decisoes", "proximas", "implementacao", "publica",
  "historico", "acoes" e similares.
- Exceções aceitáveis: nomes técnicos, slugs, URLs, comandos, identificadores
  de código, nomes de branch e trechos que precisem permanecer ASCII por
  compatibilidade.

## Documentação obrigatória

Mudanças estruturais devem atualizar a documentação no mesmo PR:

- arquitetura e decisões relevantes;
- modelo de dados e migrations;
- contrato de API quando endpoints públicos mudarem;
- instruções de operação local;
- riscos, limites e critérios de verificação.
