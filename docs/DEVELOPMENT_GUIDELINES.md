# Guia de desenvolvimento

Este projeto deve manter um histórico claro, rastreável e compatível com as
práticas comuns da comunidade open source. O histórico público não deve expor
ferramentas internas, agentes de IA ou automações usadas para apoiar a
implementação.

## Issues, branches e PRs

- Toda mudança relevante deve partir de uma issue ou documento de escopo.
- A partir da issue #11, branches novas devem usar o número da issue como eixo
  principal, não o número da fase.
- Branches devem usar nomes semânticos e neutros, sem prefixos ou sufixos de
  ferramenta, IA, agente ou fornecedor.
- Padrões recomendados:
  - `feature/<issue>-<slug>`
  - `fix/<issue>-<slug>`
  - `docs/<issue>-<slug>`
  - `refactor/<issue>-<slug>`
  - `chore/<issue>-<slug>`
- PRs devem explicar objetivo, mudanças, riscos, testes executados e próximos
  passos.
- PRs devem incluir passo a passo de teste e checklist de validação para o
  usuário ou operador.
- PRs e commits não devem usar coautoria automática de agente ou ferramenta.

## Fases e fechamento da base

- As fases 01 a 44 preservam o histórico inicial do projeto.
- O modelo de fases deve continuar apenas até a PR final de fechamento da base.
- A PR final de fechamento da base deve consolidar o estado testável inicial,
  checklist de funcionalidades, passo a passo de uso e versão semântica
  correspondente.
- Depois do fechamento da base, novas documentações devem ser organizadas por
  função, domínio, módulo, decisão ou operação, evitando uma sequência infinita
  de fases com pouco significado.
- O índice `docs/PHASE_HISTORY_INDEX.md` deve permanecer como memória histórica,
  não como mecanismo permanente de organização.

## Versionamento semântico

- O projeto deve usar tags e releases semânticas no GitHub.
- Padrão recomendado: `vMAJOR.MINOR.PATCH`.
- Enquanto o produto ainda estiver em base interna/pre-produto, usar versões
  `v0.x.y`.
- A primeira base testável deve gerar uma tag/release, por exemplo `v0.1.0`.
- Correções sem mudança de escopo incrementam PATCH.
- Novas capacidades compatíveis incrementam MINOR.
- Quebras de contrato público ou mudanças incompatíveis incrementam MAJOR
  quando o produto estiver maduro.

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
