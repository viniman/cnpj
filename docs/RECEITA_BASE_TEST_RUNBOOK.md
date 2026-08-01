# Runbook de Teste da Base Receita/Postgres

Este runbook consolida o caminho atual para testar a base da Receita Federal no
projeto local. Ele cobre o que já está pronto para validar hoje: snapshot
baixado, plano Postgres, preflight, smoke import, contagens e carga completa.

## Estado esperado

- Repositório em `main`.
- Snapshot local em `data/downloads/receita/2026-07`.
- 37 ZIPs oficiais reconhecidos.
- Postgres local disponível via `docker compose`.
- App Python disponível em `http://127.0.0.1:8000/`.

## 1. Validar scripts e testes focados

```powershell
python -m unittest tests.test_postgres_staging tests.test_postgres_snapshot_plan tests.test_receita_staging_preflight tests.test_postgres_migrations
node --check static\app.js
```

Critério de aceite:

- Os testes devem terminar com `OK`.
- O `node --check` não deve retornar erro.

## 2. Validar snapshot baixado sem Docker

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_preflight.ps1 `
  -Snapshot 2026-07 `
  -SkipDockerCheck
```

Critério de aceite:

- `status` deve ser `pass`.
- `recognized_files` deve ser `37`.
- `planned_files` deve ser `37`.
- `missing_expected_files` deve estar vazio.

## 3. Testar o painel interno

Suba o app:

```powershell
python -m radar_cnpj.server
```

Abra `http://127.0.0.1:8000/` e siga:

1. Entrar em `Importação`.
2. Informar snapshot `2026-07`.
3. Clicar em `Gerar plano` na seção `Plano PostgreSQL staging`.
4. Conferir métricas de arquivos locais, conhecidos, ausentes e volume local.
5. Conferir as métricas de capacidade:
   - `Disco livre`;
   - `Disco minimo`.
6. Conferir os botões:
   - `Copiar preflight sem Docker`;
   - `Copiar preflight completo`;
   - `Copiar smoke import`;
   - `Copiar importação completa`.
7. Copiar `Copiar preflight sem Docker` e executar no terminal.

Critério de aceite:

- A tela deve mostrar plano para o snapshot.
- A tela deve mostrar capacidade de disco para carga completa.
- Os botões devem copiar comandos válidos.
- O comando copiado deve reproduzir o preflight com `status: pass`.

## 4. Subir Postgres local

```powershell
docker compose up -d postgres
```

Aplicar migrations:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\apply_postgres_migrations.ps1
```

Critério de aceite:

- O serviço `postgres` deve estar ativo.
- O script deve aplicar ou pular migrations sem erro.
- Se o Docker Desktop/Linux engine não estiver ativo, esta etapa vai falhar e a
  importação real deve aguardar o Docker ser iniciado.

## 5. Rodar smoke import

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas
```

Critério de aceite:

- O script deve importar os arquivos de domínio selecionados.
- A saída deve indicar progresso por arquivo.
- Não deve haver erro de `COPY`, encoding ou tabela inexistente.

## 6. Validar contagens do smoke import

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -Families cnaes,municipios,naturezas `
  -RequireData
```

Critério de aceite:

- `cnaes_raw`, `municipios_raw` e `naturezas_raw` devem ter contagem maior que
  zero.
- O script deve terminar com `Validacao de contagens concluida.`

## 6.1. Consultar status consolidado

Para ver o estado atual da base, o próximo gate e as contagens do smoke test em
um único comando:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_base_status.ps1 `
  -Snapshot 2026-07
```

Critério de aceite:

- O relatório deve mostrar o `status` consolidado.
- O relatório deve mostrar o próximo gate.
- Quando o Postgres local estiver em execução, as contagens de `cnaes`,
  `municipios` e `naturezas` devem ser verificadas.

## 7. Rodar importação completa

Antes de rodar esta etapa, confirme espaço em disco suficiente para:

- os ZIPs oficiais já baixados;
- a extração temporária de cada arquivo;
- o crescimento do volume Docker/Postgres.

Na validação de 2026-08-01, o ambiente local tinha cerca de 6,5 GB livres no D:
e 7,2 GB livres no C:, enquanto o snapshot compactado `2026-07` tinha 7,64 GB.
Esse ambiente validou o smoke import, mas não tinha capacidade segura para a
carga completa.

O script de importação completa roda o preflight automaticamente. Se o check
`disk_capacity` retornar `fail`, a carga completa não começa.

Depois do smoke test passar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\import_postgres_staging_snapshot.ps1 `
  -Snapshot 2026-07
```

Critério de aceite:

- O script deve percorrer os 37 ZIPs reconhecidos.
- A carga deve terminar sem erro.
- O tempo pode ser alto porque a base local tem cerca de 7,64 GB compactados.

## 8. Validar contagens completas

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_receita_staging_counts.ps1 `
  -Snapshot 2026-07 `
  -RequireData
```

Critério de aceite:

- Todas as famílias devem ter contagem maior que zero:
  - `cnaes`;
  - `motivos`;
  - `municipios`;
  - `naturezas`;
  - `paises`;
  - `qualificacoes`;
  - `simples`;
  - `empresas`;
  - `estabelecimentos`;
  - `socios`.

## Checklist de aceite manual

- [ ] Preflight sem Docker passa com 37 arquivos.
- [ ] Painel interno gera plano do snapshot `2026-07`.
- [ ] Botões de cópia do painel funcionam.
- [ ] Postgres local sobe via Docker.
- [ ] Migrations aplicam sem drift de checksum.
- [ ] Smoke import passa.
- [ ] Contagens do smoke import são maiores que zero.
- [ ] Espaço em disco suficiente para carga completa.
- [ ] Preflight completo passa em `disk_capacity`.
- [ ] Importação completa passa.
- [ ] Contagens completas são maiores que zero.

## Limitações atuais

- A importação completa ainda é operada por script, não por job assíncrono no
  painel.
- A barra de progresso visual da migração ainda não existe.
- A validação real com Postgres depende do Docker Desktop/Linux engine ativo.
- Os dados ainda entram no schema bruto `receita_staging`; a normalização para
  schemas operacionais será uma etapa posterior.
- O ambiente local usado nesta validação não tinha espaço livre suficiente para
  a carga completa.
