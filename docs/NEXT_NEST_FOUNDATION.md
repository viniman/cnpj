# Fundação Next.js e NestJS

Esta é a primeira estrutura do futuro produto fora do super admin Python.

## Papéis

- `apps/api`: backend NestJS. Será dono da API operacional, autenticação,
  permissões, Prisma, CRM, campanhas, listas e contratos públicos.
- `apps/web`: frontend Next.js. Será a experiência principal com SSR e sem
  expor consultas sensíveis diretamente no cliente.
- Python atual: permanece como super admin interno, ETL da Receita e scripts de
  importação até os fluxos equivalentes estarem maduros.

## Instalação futura

Não instalei `node_modules` nesta PR para preservar espaço local. Quando for
rodar:

```powershell
npm install
```

Depois:

```powershell
npm run dev:api
npm run dev:web
```

URLs esperadas:

```text
NestJS: http://127.0.0.1:3001/health
Next.js: http://127.0.0.1:3000/
```

## Banco

O Prisma começa com `DATABASE_URL` em `apps/api/.env.example`.

O schema `receita_staging` continua bruto e não deve ser remodelado diretamente
pelo Prisma. As próximas PRs devem criar modelos operacionais em schema próprio
ou no schema público, lendo `receita_staging` como fonte de transformação.

## Próximas PRs

1. Definir schema operacional inicial no Prisma.
2. Criar service Nest para busca de empresas no Postgres.
3. Criar página Next SSR de busca.
4. Migrar gradualmente fluxos de usuário final para Next.
5. Manter Python para ETL/super admin até substituição explícita.
