# Fundação Next.js e NestJS

Esta é a primeira estrutura do futuro produto fora do super admin Python.

## Papéis

- `apps/api`: backend NestJS. Será dono da API operacional, autenticação,
  permissões, Prisma, CRM, campanhas, listas e contratos públicos.
- `apps/web`: frontend Next.js. Será a experiência principal com SSR e sem
  expor consultas sensíveis diretamente no cliente.
- Python atual: permanece como super admin interno, ETL da Receita e scripts de
  importação até os fluxos equivalentes estarem maduros.

## Instalação

As dependências Node foram instaladas com cache local em `data/npm-cache/`.
Para instalar novamente:

```powershell
npm.cmd install --cache .\data\npm-cache
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

Validações executadas na fundação:

```powershell
npm.cmd --workspace apps/api run build
npm.cmd --workspace apps/web run build
python -m unittest tests.test_next_nest_foundation
```

Observação de segurança: `npm audit --omit=dev` ainda aponta vulnerabilidades
em dependências transitivas do Next (`postcss`/`sharp`) na versão disponível.
Não foi aplicado `npm audit fix --force` porque a sugestão de correção envolve
downgrade/breaking change inadequado para esta fundação.

## Banco

O `DATABASE_URL` em `apps/api/.env` aponta para o schema Postgres `app`
(`?schema=app`), usando o preview feature `multiSchema` do Prisma.

O schema `receita_staging` continua bruto e não é remodelado pelo Prisma.
`CompaniesService` (issue #66) lê `receita_staging` via SQL parametrizado
(`prisma.$queryRaw`), não via modelos Prisma — ver
`docs/ARCHITECTURE.md` para o desenho da query e o índice adicionado para
viabilizar o join.

## Frontend do produto (Radar CNPJ)

`apps/web` deixou de ser só a fundação SSR e passou a ser o início real da
plataforma Radar CNPJ (produto SaaS da empresa Radar, ver ADR-050 em
`docs/DECISIONS.md`), sem autenticação ainda (uso interno). Issue #68
adicionou:

- Tailwind CSS (`tailwind.config.ts`, `postcss.config.mjs`) — não existia
  antes.
- Shell com navegação lateral: `Empresas`, `Listas`, `Campanhas`,
  `Config. de e-mail` (`components/sidebar.tsx`).
- `/empresas`: página funcional que consome `GET /companies/search` do
  lado do cliente (`NEXT_PUBLIC_API_URL`), com filtros de nome/CNPJ, UF,
  CNAE e situação cadastral.
- `/listas`, `/campanhas`, `/config/email`: placeholders premium
  ("Em construção"), aguardando as issues seguintes.

Referência de produto usada no design: mapeamento dos módulos Leads,
Localizador e Campanhas do Snov.io (não copiado literalmente — layout
próprio, mais limpo).

Issue #70 tornou `/listas` funcional:

- Modelos Prisma `List` e `ListCompany` (schema `app`). `ListCompany`
  guarda um snapshot dos campos de exibição no momento em que a empresa
  foi adicionada (não depende de novo join com `receita_staging`, que
  pode ser lento por cache frio).
- Sem escopo por organização ainda — listas são globais neste MVP sem
  autenticação.
- `/empresas` ganhou seleção de linhas + "Salvar em lista" (lista
  existente ou nova). `/listas` lista as listas salvas. `/listas/[id]`
  mostra e permite remover empresas de uma lista.

Issue #72 tornou `/config/email` funcional:

- Modelo Prisma `EmailAccount`: remetente, credenciais SMTP, limite
  diário de envios, fuso horário de redefinição, modo de atraso entre
  envios (fixo em segundos ou faixa aleatória min-max).
- A senha SMTP é criptografada em repouso (AES-256-GCM,
  `apps/api/src/common/crypto.util.ts`, chave via
  `EMAIL_CREDENTIALS_KEY`) e a API nunca retorna o valor em texto puro
  em nenhum endpoint, nem no `create`/`update`.
- `POST /email-accounts/:id/test` valida a conexão SMTP de verdade via
  `nodemailer.verify()` — testado contra o SMTP real do AWS SES.
- UI em `/config/email`: cards com as contas configuradas, formulário de
  criação com os campos de throttle, botão "Testar conexão" com
  resultado inline.

## Próximas PRs

1. ~~Definir schema operacional inicial no Prisma.~~ Feito (issue #66):
   `app.organizations`, `app.users`.
2. ~~Criar service Nest para busca de empresas no Postgres.~~ Feito (issue
   #66): `GET /companies/search`.
3. ~~Criar página Next SSR de busca.~~ Feito parcialmente (issue #68):
   `/empresas` busca client-side; SSR pode vir depois se necessário.
4. ~~Listas (Prisma + endpoints + UI).~~ Feito (issue #70).
5. ~~Config de conta de e-mail (SMTP AWS SES + limite diário/atraso).~~
   Feito (issue #72).
6. Campanhas + motor de envio — depende de 4 e 5 (ambos feitos), próxima
   issue.
7. Migrar gradualmente fluxos de usuário final para Next.
8. Manter Python para ETL/super admin até substituição explícita.
