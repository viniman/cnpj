# PR - Issue 11: Governança pós-base e versionamento semântico

Issue: https://github.com/viniman/cnpj/issues/11

## Contexto

As fases documentadas preservaram a fundação inicial do projeto, mas não devem
virar uma sequência infinita. Esta PR registra a transição para organização por
issues, PRs, módulos, documentos de domínio, ADRs e versionamento semântico.

## Mudanças

- Branches novas passam a usar o número da issue como eixo principal.
- O modelo de fases deve encerrar após a PR final de fechamento da base.
- A documentação futura deve ser organizada por função, domínio, módulo,
  operação ou decisão.
- Releases/tags semânticas passam a fazer parte da governança.
- PRs devem trazer passo a passo de teste e checklist de validação.

## Passo a Passo de Teste

1. Abrir `docs/DEVELOPMENT_GUIDELINES.md`.
2. Confirmar o padrão `feature/<issue>-<slug>`.
3. Confirmar a seção de fechamento da base.
4. Confirmar a seção de versionamento semântico.
5. Abrir `docs/NEXT_ARCHITECTURE_LEDGER.md`.
6. Confirmar que a PR final da base terá checklist, passo a passo e release.

## Checklist

- [x] Regra de branch por issue documentada.
- [x] Encerramento futuro do modelo de fases documentado.
- [x] Versionamento semântico documentado.
- [x] Exigência de passo a passo e checklist em PRs documentada.
- [x] Sem mudanças de runtime.
