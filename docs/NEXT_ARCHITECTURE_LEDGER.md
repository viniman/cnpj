# Livro razão de arquitetura e próximas fases

Este documento consolida as decisões tomadas após a fase 41, antes da migração
real para PostgreSQL e antes da separação entre super admin, produto cliente e
API pública. Ele funciona como fonte de contexto para as próximas issues e PRs.

## Norte do produto

O Radar CNPJ deve evoluir de um buscador local para uma plataforma de
inteligência comercial B2B baseada em dados públicos, histórico cadastral,
qualidade de contato, cadências de prospecção e API monetizável.

O diferencial não deve ser apenas "consultar CNPJ". O produto deve explicar
mudanças, indicar timing comercial, limpar listas e transformar dados públicos
em decisões comerciais auditáveis.

## Arquitetura alvo

Decisão atual:

- PostgreSQL passa a ser o banco central de escala.
- O banco pode começar como uma única instância com schemas separados.
- Python permanece como motor de ETL, download, parsing, processamento de
  arquivos grandes e jobs recorrentes da Receita.
- NestJS deve ser o backend principal do produto operacional e dono das
  migrations Prisma das tabelas de produto.
- Next.js deve ser a interface premium do cliente e, futuramente, também pode
  hospedar um super admin melhor.
- O SQLite deve virar legado/teste local e sair do caminho principal após a
  migração para Postgres.

Schemas iniciais recomendados no mesmo Postgres:

- `receita_staging`: cópia bruta controlada dos arquivos oficiais da Receita.
- `app`: empresas normalizadas, listas, leads, cadências, templates, CRM,
  usuários, workspaces e regras de produto.
- `billing`: planos, créditos, assinaturas, API keys e consumo.
- `audit`: eventos auditáveis, exportações, ações de usuário, jobs e decisões
  automatizadas.

Essa separação por schema reduz infraestrutura agora e permite separar bancos
ou servidores no futuro caso volume, backup, segurança ou performance exijam.

## Papel do staging

Staging não é a fonte oficial em si. A fonte oficial continua sendo o arquivo
publicado pela Receita Federal/SERPRO. O staging é uma cópia bruta controlada,
com colunas próximas do layout oficial e metadados operacionais, como:

- snapshot;
- chunk;
- arquivo de origem;
- data de carga;
- índices de busca/correlação;
- logs de execução.

O staging existe para evitar que arquivos brutos, transformações de produto e
listas de usuário fiquem misturados. O fluxo alvo é:

```text
Receita Federal ZIP/CSV
-> receita_staging
-> transformações/diffs
-> app.operacional
-> busca, listas, API, cadências e CRM
```

## Histórico mensal e diffs

O produto deve manter snapshots mensais da Receita quando disponíveis. A carga
inicial prioriza o snapshot mais recente. Depois disso, jobs recorrentes devem:

1. verificar se existe snapshot novo;
2. baixar arquivos ausentes;
3. importar para staging;
4. calcular diferenças por CNPJ;
5. materializar mudanças relevantes no operacional;
6. gerar alertas comerciais.

Mudanças históricas importantes:

- entrada e saída de sócios;
- alteração de razão social ou nome fantasia;
- mudança de situação cadastral;
- mudança de endereço, cidade ou UF;
- alteração de CNAE principal ou secundário;
- alteração de capital social;
- mudança de porte;
- opção ou exclusão do Simples/MEI;
- abertura ou fechamento de matriz/filial;
- alteração de email ou telefone público.

Histórico societário, especialmente sócios que saíram, deve ser tratado como
diferencial de produto e não apenas como dado auxiliar.

## Banco, migrations e ownership

Ownership recomendado:

- `receita_staging`: SQL migrations versionadas, próximas do layout oficial.
- `app`, `billing` e parte operacional: Prisma migrations no NestJS.
- Python executa ETL e jobs, mas não deve criar schema operacional de forma
  ad hoc.

Convenção de nomes:

- bootstrap Docker: `infra/postgres/init/001_bootstrap.sql`;
- staging SQL: `infra/postgres/migrations/YYYYMMDDHHMMSS_descriptive_slug.sql`;
- produto Prisma:
  `apps/api/prisma/migrations/YYYYMMDDHHMMSS_descriptive_slug/migration.sql`.

Se Python precisar consultar ou escrever dados operacionais, a preferência é:

1. usar APIs/contratos internos do NestJS quando a regra for de produto;
2. usar acesso direto ao staging quando a regra for ETL/dado bruto;
3. evitar duplicar regras de negócio entre Python e NestJS.

## Super admin e interfaces

O painel Python atual deve ser tratado como laboratório/super admin temporário.
Ele pode continuar existindo enquanto:

- a importação Postgres não estiver completa;
- o painel Next ainda não cobrir os fluxos de cliente;
- os jobs de ETL ainda precisarem de uma interface interna simples.

A migração de UI deve seguir esta ordem:

1. Postgres e pipeline de dados.
2. Separação de rotas e responsabilidades no painel atual.
3. Next.js para produto cliente.
4. Next.js para super admin, se fizer sentido.
5. Remoção gradual de telas de cliente do Python.

Mesmo sendo interno, o super admin deve ter UX clara, navegação previsível,
páginas menores e documentação própria de front.

## API AI-first e monetização

O CNPJ Search deve nascer com contrato público preparado para agentes e
integrações automatizadas:

- OpenAPI;
- `llms.txt`;
- exemplos de consulta;
- API keys;
- escopos;
- rate limit;
- consumo de créditos;
- primeiros usos gratuitos;
- cobrança após limite gratuito;
- logs de uso e erros explícitos.

Renderização server-side no Next.js ajuda a proteger experiência e navegação,
mas a proteção real dos dados vem de autenticação, autorização, rate limit,
escopos, billing e auditoria no backend.

## BrasilAPI

BrasilAPI deve permanecer como fonte complementar, não como base principal.
Usos aceitáveis:

- consulta individual pontual;
- fallback;
- debug;
- comparação de payload;
- validação de CNPJ durante desenvolvimento.

O produto principal deve depender da base oficial importada e historizada no
Postgres.

## Padrões de nomenclatura de produto

- "Sequências" deve migrar para "Cadências" no produto, na documentação e no
  novo schema Postgres.
- Nomes novos devem seguir o domínio comercial em português na UI e nomes
  técnicos consistentes no backend, como `cadences`, `cadence_steps` e
  `cadence_enrollments`.
- Mudanças grandes de nomenclatura devem ser feitas agora, antes de consolidar
  o schema operacional em Postgres.

## Diferenciais futuros do produto

1. Linha do tempo completa da empresa.
2. Alertas de mudança cadastral e societária.
3. Histórico de sócios antigos, entradas e saídas.
4. Grafo societário entre sócios, empresas, grupos, endereços e contadores.
5. Detecção de email de contador, escritório fiscal e contato terceirizado.
6. Score de oportunidade comercial.
7. Eventos de timing comercial.
8. ICP vivo que aprende com respostas, reuniões e conversões.
9. Listas limpas automaticamente.
10. Cadências integradas ao dado público, ICP e timing.
11. CRM automático de leads quentes.
12. API AI-first com `llms.txt`, OpenAPI e exemplos para agentes.
13. Explicação "por que esse lead?".
14. Monitoramento de mercado por segmento, CNAE, cidade e UF.
15. Comparação com clientes atuais para descobrir padrões reais de ICP.
16. Radar de concorrentes, clientes e contas-alvo.
17. Qualidade de dados transparente por fonte, data e confiança.
18. Histórico mensal como produto premium.

## Próximas fases recomendadas

1. Criar migrations SQL reais do `receita_staging`.
2. Implementar job Python de carga Postgres com progresso de download e COPY.
3. Validar importação completa do snapshot mais recente.
4. Criar modelo de diff mensal da Receita.
5. Criar schema operacional inicial em NestJS/Prisma.
6. Migrar busca de empresas para Postgres.
7. Renomear sequências para cadências.
8. Criar dicionário completo do banco.
9. Criar documentação de API pública e `llms.txt`.
10. Criar guia de interface premium para Next.js e super admin.

## Encerramento da base e governança futura

As fases documentadas são úteis para preservar a construção inicial da base, mas
não devem virar o mecanismo permanente de organização do projeto. Ao finalizar a
base testável, o repositório deve ter uma última PR de fechamento da base com:

- checklist de funcionalidades disponíveis;
- passo a passo completo de teste;
- limitações conhecidas;
- documentação de operação local;
- tag/release semântica no GitHub.

Depois disso, novas iniciativas devem ser rastreadas principalmente por issues,
PRs, módulos, documentos de domínio e ADRs. Branches devem usar o número da
issue como eixo principal, por exemplo `feature/12-import-receita-copy`, em vez
de continuar criando fases indefinidamente.
