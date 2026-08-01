# Auditoria de Readiness da Base

Este documento consolida o estado atual da base Receita/Postgres e define os
critérios objetivos para a futura PR de fechamento da base.

## Status em 2026-08-01

Status geral: **smoke import real validado, carga completa aguardando capacidade
de disco**.

Motivo:

- O snapshot local `2026-07` foi validado com preflight e planner.
- O painel interno já expõe comandos de preflight, smoke import e importação
  completa.
- Os scripts de importação e contagem existem e têm cobertura focada.
- O Docker Desktop/Linux engine foi iniciado e o smoke import real foi validado.
- A carga completa ainda não deve ser executada neste ambiente porque o espaço
  livre medido é menor que o necessário para ZIPs, extrações temporárias e
  volume Postgres.

## Evidências já validadas

### Repositório

- Branch local ativa: `main`.
- Branch remota principal: `origin/main`.
- Branches antigas de trabalho removidas.
- Issues abertas no momento da auditoria: nenhuma antes da issue desta
  auditoria.

### Snapshot local

Comando validado:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 `
  -Snapshot 2026-07 `
  -SkipDockerCheck
```

Resultado observado:

- `status`: `pass`;
- `recognized_files`: `37`;
- `total_bytes`: `7643363104`;
- `planned_files`: `37`;
- `missing_expected_files`: vazio.

Famílias reconhecidas:

- `cnaes`: 1 arquivo;
- `motivos`: 1 arquivo;
- `municipios`: 1 arquivo;
- `naturezas`: 1 arquivo;
- `paises`: 1 arquivo;
- `qualificacoes`: 1 arquivo;
- `simples`: 1 arquivo;
- `empresas`: 10 arquivos;
- `estabelecimentos`: 10 arquivos;
- `socios`: 10 arquivos.

### Testes focados

Comando validado:

```powershell
python -m unittest tests.test_postgres_staging tests.test_postgres_snapshot_plan tests.test_receita_staging_preflight tests.test_postgres_migrations
```

Resultado observado:

```text
Ran 21 tests
OK
```

Validação do front:

```powershell
node --check static\app.js
```

Resultado observado: sem erro de sintaxe.

### Smoke import real

Comando validado:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

Contagens validadas:

```text
cnaes              cnaes_raw                            1359
municipios         municipios_raw                       5572
naturezas          naturezas_raw                          91
Validacao de contagens concluida.
```

Reimportação idempotente validada:

- `DELETE 1359` seguido de `INSERT 0 1359`;
- `DELETE 5572` seguido de `INSERT 0 5572`;
- `DELETE 91` seguido de `INSERT 0 91`.

### Capacidade de disco

Espaço medido antes da carga completa:

- D: cerca de 6,5 GB livres;
- C: cerca de 7,2 GB livres;
- snapshot `2026-07` compactado: 7,64 GB.

Conclusão: a carga completa precisa de mais espaço antes de ser executada.

### Gate automático de disco

O preflight agora calcula `disk_capacity` com multiplicador padrão `3.0` sobre
o tamanho compactado reconhecido. No ambiente atual:

```text
total_bytes:    7643363104
free_bytes:     6492880896
required_bytes: 22930089312
status:         fail
```

O comando de carga completa chama esse preflight automaticamente e não inicia a
importação quando o gate falha.

## Issues e PRs que compõem a base testável

| Issue | PR | Escopo | Estado |
| --- | --- | --- | --- |
| #11 | #12 | Governança pós-fases, issues, PRs e versionamento semântico | Mergeado |
| #13 | #14 | Importação de arquivo oficial para Postgres staging | Mergeado |
| #15 | #16 | Comando de importação por arquivo no painel | Mergeado |
| #17 | #18 | Importação de snapshot completo por script | Mergeado |
| #19 | #20 | Preflight da base Receita/Postgres | Mergeado |
| #21 | #22 | Comandos de preflight/snapshot no painel | Mergeado |
| #23 | #24 | Validação de contagens pós-importação | Mergeado |
| #25 | #26 | Runbook consolidado de teste da base | Mergeado |

## O que já está pronto para o usuário testar

- Baixar/descobrir arquivos oficiais pelo fluxo atual do app Python.
- Gerar plano PostgreSQL staging pelo painel.
- Copiar comandos do painel para:
  - preflight sem Docker;
  - preflight completo;
  - smoke import;
  - importação completa.
- Rodar preflight da base local.
- Planejar carga completa de 37 ZIPs.
- Executar smoke import quando Docker/Postgres estiverem ativos.
- Validar contagens por família/tabela depois da importação.

## Gates pendentes para a PR final de fechamento da base

A PR final de fechamento da base só deve ser criada depois destes gates:

- [ ] Docker Desktop/Linux engine ativo.
- [ ] `docker compose up -d postgres` concluído.
- [ ] `scripts\apply_postgres_migrations.ps1` executado sem erro.
- [x] Smoke import executado:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

- [x] Contagens do smoke import validadas:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas `
  -RequireData
```

- [ ] Capacidade de disco suficiente provisionada para ZIPs, extrações
  temporárias e volume Postgres.
- [x] Gate automático impede carga completa quando o disco está insuficiente.
- [ ] Importação completa executada:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07
```

- [ ] Contagens completas validadas:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -RequireData
```

- [ ] Runbook `docs/RECEITA_BASE_TEST_RUNBOOK.md` executado e marcado.
- [ ] Tag/release semântica criada depois do merge da PR final.

## Versão semântica sugerida

Quando os gates acima passarem, a primeira release da base pode ser:

```text
v0.1.0
```

Motivo:

- Ainda é uma base inicial interna.
- Já terá importação oficial da Receita para Postgres staging.
- Ainda não terá NextJS/NestJS, login, billing, CRM final ou automação de email
  completa.

## Próxima issue recomendada

Quando o Docker estiver ativo, criar uma issue com escopo:

```text
test: validar smoke import real da base Receita
```

Critério de fechamento:

- Smoke import executado no Postgres.
- Contagens maiores que zero para `cnaes`, `municipios` e `naturezas`.
- Evidência registrada no PR.

Depois disso, criar a issue final:

```text
chore: fechar base inicial Receita/Postgres
```

Essa última PR deve apenas consolidar evidências, atualizar o checklist final e
preparar a tag `v0.1.0`.
