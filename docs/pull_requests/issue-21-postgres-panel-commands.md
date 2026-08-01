# PR - Issue 21: Comandos de preflight e snapshot no painel

Issue: https://github.com/viniman/cnpj/issues/21

Closes #21

## Contexto

A issue #19 criou o preflight local da base Receita/Postgres. Esta PR leva os
comandos principais para o payload do plano PostgreSQL e para a tela interna de
importação, deixando o teste manual mais direto.

## Mudanças

- Adiciona `commands` ao retorno de `GET /api/sources/official/postgres-plan`.
- Expõe comandos de preflight completo, preflight sem Docker, smoke import e
  importação completa.
- Adiciona botões de cópia na seção `Plano PostgreSQL staging`.
- Mantém os comandos por arquivo já existentes.
- Atualiza testes de API/front estático.

## Passo a Passo de Teste

1. Rodar validações automatizadas:

```powershell
python -m unittest tests.test_postgres_staging tests.test_postgres_migrations
node --check static\app.js
```

2. Rodar o app local:

```powershell
python -m radar_cnpj.server
```

3. Abrir `http://127.0.0.1:8000/`, entrar em `Importação`, informar snapshot
   `2026-07` e clicar em `Gerar plano`.

4. Conferir que a seção `Plano PostgreSQL staging` mostra botões para copiar:

- `Copiar preflight sem Docker`;
- `Copiar preflight completo`;
- `Copiar smoke import`;
- `Copiar importação completa`.

5. Colar no terminal o comando copiado em `Copiar preflight sem Docker` e
   validar que ele retorna `status: pass`, `recognized_files: 37` e
   `planned_files: 37`.

## Checklist

- [x] API inclui comandos de snapshot no plano Postgres.
- [x] UI renderiza botões de cópia para os comandos principais.
- [x] Comandos por arquivo continuam disponíveis.
- [x] Testes automatizados atualizados.
- [x] Passo a passo de teste manual documentado.
- [ ] Execução real do smoke import com Docker/Postgres ativo.
