# PR - Issue 53: Visualização mínima do Postgres staging no Python

## Contexto

A base parcial real da Receita já existe em `receita_staging`, mas a tela
`Empresas` do Python continua lendo o SQLite operacional. Antes de iniciar
Next/Nest, precisamos de uma forma mínima de conferir os dados reais importados
pela interface atual.

Issue: #53

## Implementado

- Adiciona `GET /api/postgres/staging/summary`.
- Adiciona `GET /api/postgres/staging/companies`.
- Adiciona aba `Receita DB` no super admin Python.
- Mostra contagens por família importada.
- Permite busca limitada por razão social, CNPJ, sócio, e-mail, UF, município,
  CNAE principal e presença de e-mail.
- Mantém a tela `Empresas` antiga intacta.
- Não normaliza dados nem altera o schema operacional.

## Como verificar

Com Postgres/Docker ativo:

```powershell
python -m unittest tests.test_server_routes tests.test_postgres_migrations
node --check static\app.js
```

Validar endpoints reais:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/postgres/staging/summary?snapshot=2026-07"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/postgres/staging/companies?snapshot=2026-07&state=SP&has_email=1&limit=5"
```

Validar na interface:

1. Abrir `http://127.0.0.1:8000/`.
2. Entrar em `Receita DB`.
3. Conferir as contagens por família.
4. Filtrar por `UF = SP`.
5. Marcar `Com email`.
6. Clicar em `Buscar`.
7. Conferir razão social, CNPJ, e-mail, CNAE, sócios e sócio de amostra.

## Resultado validado

```text
cnaes                 1.359
empresas          4.494.860
estabelecimentos  4.753.435
motivos                  63
municipios            5.572
naturezas                91
paises                  255
qualificacoes            68
simples          49.445.426
socios            2.019.150
```

Endpoint de empresas validado com `state=SP&has_email=1&limit=5`, retornando
registros reais com CNPJ, e-mail e sócio.

## Checklist

- [x] Branch criada a partir da issue.
- [x] Nome da branch não usa prefixo de IA.
- [x] Endpoint de resumo criado.
- [x] Endpoint de busca criado.
- [x] Aba mínima no Python criada.
- [x] Tela `Empresas` antiga preservada.
- [x] Testes automatizados adicionados.
- [x] Passo a passo de teste documentado.

## Observações

- Esta é uma ponte temporária para validação interna.
- O produto final deve consumir o Postgres via NestJS/Prisma e renderizar a
  experiência principal em Next.js.
