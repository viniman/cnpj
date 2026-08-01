# PR - Issue 42: Capacidade de disco no painel Postgres

Issue: https://github.com/viniman/cnpj/issues/42

Closes #42

## Contexto

O preflight já bloqueia a carga completa quando o disco está insuficiente, mas o
painel interno ainda não mostrava esse status antes do usuário copiar comandos.
Esta PR leva o gate de capacidade para o payload do plano Postgres e para a UI.

## Mudanças

- Adiciona `disk_capacity` ao retorno de `GET /api/sources/official/postgres-plan`.
- Calcula espaço livre no drive dos arquivos baixados.
- Adiciona `disk_capacity_status` ao resumo.
- Renderiza métricas `Disco livre` e `Disco minimo`.
- Adiciona guardrail visual quando a capacidade é insuficiente.
- Atualiza testes de API e front estático.

## Passo a Passo de Teste

1. Rodar testes focados:

```powershell
python -m unittest tests.test_postgres_staging tests.test_postgres_migrations
node --check static\app.js
```

2. Rodar o app:

```powershell
python -m radar_cnpj.server
```

3. Abrir `http://127.0.0.1:8000/`, entrar em `Importação`, informar snapshot
   `2026-07` e clicar em `Gerar plano`.

4. Conferir na seção `Plano PostgreSQL staging`:

- métrica `Disco livre`;
- métrica `Disco minimo`;
- guardrail de capacidade quando o status for `fail`.

## Checklist

- [x] API retorna `disk_capacity`.
- [x] UI mostra disco livre e mínimo recomendado.
- [x] Guardrail visual aparece quando falta disco.
- [x] Testes atualizados.
- [x] PR inclui passo a passo de teste.
