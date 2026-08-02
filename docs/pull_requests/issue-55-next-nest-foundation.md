# PR - Issue 55: Fundação Next.js e NestJS

## Contexto

A interface Python agora possui a aba mínima `Receita DB`, que permite validar
dados reais do Postgres staging. O próximo passo é iniciar a estrutura
Next.js/NestJS sem remover o super admin Python.

Issue: #55

## Implementado

- Adicionado `package.json` raiz com workspaces.
- Criado `apps/api` com NestJS mínimo.
- Criado `apps/web` com Next.js mínimo.
- Criado `apps/api/prisma/schema.prisma`.
- Documentado o papel de cada camada em `docs/NEXT_NEST_FOUNDATION.md`.
- Mantido Python intacto como super admin/ETL.

## Como verificar

Sem instalar dependências:

```powershell
python -m unittest tests.test_next_nest_foundation
```

Quando houver espaço para instalar dependências:

```powershell
npm install
npm run dev:api
npm run dev:web
```

Depois acessar:

```text
http://127.0.0.1:3001/health
http://127.0.0.1:3000/
```

## Checklist

- [x] Branch criada a partir da issue.
- [x] Nome da branch não usa prefixo de IA.
- [x] Estrutura `apps/api` criada.
- [x] Estrutura `apps/web` criada.
- [x] Scripts npm documentados.
- [x] Prisma inicial criado.
- [x] Python preservado.
- [x] Próximos passos documentados.

## Observações

- Esta PR não instala `node_modules`.
- A primeira implementação real de busca deve vir em PR própria, usando NestJS
  como backend e Next.js com SSR.
