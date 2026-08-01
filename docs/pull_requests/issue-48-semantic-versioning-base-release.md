# PR - Issue 48: Versionamento semântico e fechamento da base inicial

## Contexto

O projeto está encerrando o ciclo de fases numeradas e passando a usar issues,
branches, PRs e releases semânticas como trilho principal de evolução. A base
Receita/Postgres ainda depende da issue #41 para validar a carga completa em um
ambiente com capacidade.

Issue: #48

## Implementado

- Adicionado `docs/RELEASE_VERSIONING.md`.
- Documentado o checklist obrigatório da release `v0.1.0`.
- Documentado o comando de tag após a PR final de fechamento da base.
- Atualizado `docs/DEVELOPMENT_GUIDELINES.md` para apontar para o checklist de
  release.
- Atualizado `docs/BASE_READINESS_AUDIT.md` com o gate do checklist de release.
- Atualizado `README.md` com o novo documento de versionamento.

## Como verificar

```powershell
rg -n "RELEASE_VERSIONING|v0.1.0|Issue #41|versionamento semântico" README.md docs
rg -n "mojibake" docs README.md -g "*.md"
```

## Checklist

- [x] Branch criada a partir da issue.
- [x] Nome da branch não usa prefixo de IA.
- [x] Documento de versionamento semântico criado.
- [x] Checklist de fechamento da base inicial criado.
- [x] Caminho para tag `v0.1.0` documentado.
- [x] Relação com a issue #41 documentada.
- [x] PR inclui passo a passo de teste e checklist.

## Observações

- Esta PR prepara o fechamento e o versionamento, mas não cria a tag `v0.1.0`.
- A tag só deve ser criada depois que a issue #41 for concluída e a PR final da
  base inicial estiver mergeada em `main`.
