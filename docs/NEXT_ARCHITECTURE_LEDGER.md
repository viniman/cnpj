# Livro razao de arquitetura e proximas fases

Este documento consolida as decisoes tomadas apos a fase 41, antes da migracao
real para PostgreSQL e antes da separacao entre super admin, produto cliente e
API publica. Ele funciona como fonte de contexto para as proximas issues e PRs.

## Norte do produto

O Radar CNPJ deve evoluir de um buscador local para uma plataforma de
inteligencia comercial B2B baseada em dados publicos, historico cadastral,
qualidade de contato, cadencias de prospeccao e API monetizavel.

O diferencial nao deve ser apenas "consultar CNPJ". O produto deve explicar
mudancas, indicar timing comercial, limpar listas e transformar dados publicos
em decisoes comerciais auditaveis.

## Arquitetura alvo

Decisao atual:

- PostgreSQL passa a ser o banco central de escala.
- O banco pode comecar como uma unica instancia com schemas separados.
- Python permanece como motor de ETL, download, parsing, processamento de
  arquivos grandes e jobs recorrentes da Receita.
- NestJS deve ser o backend principal do produto operacional e dono das
  migrations Prisma das tabelas de produto.
- Next.js deve ser a interface premium do cliente e, futuramente, tambem pode
  hospedar um super admin melhor.
- O SQLite deve virar legado/teste local e sair do caminho principal apos a
  migracao para Postgres.

Schemas iniciais recomendados no mesmo Postgres:

- `receita_staging`: copia bruta controlada dos arquivos oficiais da Receita.
- `app`: empresas normalizadas, listas, leads, cadencias, templates, CRM,
  usuarios, workspaces e regras de produto.
- `billing`: planos, creditos, assinaturas, API keys e consumo.
- `audit`: eventos auditaveis, exportacoes, acoes de usuario, jobs e decisoes
  automatizadas.

Essa separacao por schema reduz infraestrutura agora e permite separar bancos
ou servidores no futuro caso volume, backup, seguranca ou performance exijam.

## Papel do staging

Staging nao e a fonte oficial em si. A fonte oficial continua sendo o arquivo
publicado pela Receita Federal/SERPRO. O staging e uma copia bruta controlada,
com colunas proximas do layout oficial e metadados operacionais, como:

- snapshot;
- chunk;
- arquivo de origem;
- data de carga;
- indices de busca/correlacao;
- logs de execucao.

O staging existe para evitar que arquivos brutos, transformacoes de produto e
listas de usuario fiquem misturados. O fluxo alvo e:

```text
Receita Federal ZIP/CSV
-> receita_staging
-> transformacoes/diffs
-> app.operacional
-> busca, listas, API, cadencias e CRM
```

## Historico mensal e diffs

O produto deve manter snapshots mensais da Receita quando disponiveis. A carga
inicial prioriza o snapshot mais recente. Depois disso, jobs recorrentes devem:

1. verificar se existe snapshot novo;
2. baixar arquivos ausentes;
3. importar para staging;
4. calcular diferencas por CNPJ;
5. materializar mudancas relevantes no operacional;
6. gerar alertas comerciais.

Mudancas historicas importantes:

- entrada e saida de socios;
- alteracao de razao social ou nome fantasia;
- mudanca de situacao cadastral;
- mudanca de endereco, cidade ou UF;
- alteracao de CNAE principal ou secundario;
- alteracao de capital social;
- mudanca de porte;
- opcao ou exclusao do Simples/MEI;
- abertura ou fechamento de matriz/filial;
- alteracao de email ou telefone publico.

Historico societario, especialmente socios que sairam, deve ser tratado como
diferencial de produto e nao apenas como dado auxiliar.

## Banco, migrations e ownership

Ownership recomendado:

- `receita_staging`: SQL migrations versionadas, proximas do layout oficial.
- `app`, `billing` e parte operacional: Prisma migrations no NestJS.
- Python executa ETL e jobs, mas nao deve criar schema operacional de forma
  ad hoc.

Se Python precisar consultar ou escrever dados operacionais, a preferencia e:

1. usar APIs/contratos internos do NestJS quando a regra for de produto;
2. usar acesso direto ao staging quando a regra for ETL/dado bruto;
3. evitar duplicar regras de negocio entre Python e NestJS.

## Super admin e interfaces

O painel Python atual deve ser tratado como laboratorio/super admin temporario.
Ele pode continuar existindo enquanto:

- a importacao Postgres nao estiver completa;
- o painel Next ainda nao cobrir os fluxos de cliente;
- os jobs de ETL ainda precisarem de uma interface interna simples.

A migracao de UI deve seguir esta ordem:

1. Postgres e pipeline de dados.
2. Separacao de rotas e responsabilidades no painel atual.
3. Next.js para produto cliente.
4. Next.js para super admin, se fizer sentido.
5. Remocao gradual de telas de cliente do Python.

Mesmo sendo interno, o super admin deve ter UX clara, navegacao previsivel,
paginas menores e documentacao propria de front.

## API AI-first e monetizacao

O CNPJ Search deve nascer com contrato publico preparado para agentes e
integracoes automatizadas:

- OpenAPI;
- `llms.txt`;
- exemplos de consulta;
- API keys;
- escopos;
- rate limit;
- consumo de creditos;
- primeiros usos gratuitos;
- cobranca apos limite gratuito;
- logs de uso e erros explicitos.

Renderizacao server-side no Next.js ajuda a proteger experiencia e navegacao,
mas a protecao real dos dados vem de autenticacao, autorizacao, rate limit,
escopos, billing e auditoria no backend.

## BrasilAPI

BrasilAPI deve permanecer como fonte complementar, nao como base principal.
Usos aceitaveis:

- consulta individual pontual;
- fallback;
- debug;
- comparacao de payload;
- validacao de CNPJ durante desenvolvimento.

O produto principal deve depender da base oficial importada e historizada no
Postgres.

## Padroes de nomenclatura de produto

- "Sequencias" deve migrar para "Cadencias" no produto, na documentacao e no
  novo schema Postgres.
- Nomes novos devem seguir o dominio comercial em portugues na UI e nomes
  tecnicos consistentes no backend, como `cadences`, `cadence_steps` e
  `cadence_enrollments`.
- Mudancas grandes de nomenclatura devem ser feitas agora, antes de consolidar
  o schema operacional em Postgres.

## Diferenciais futuros do produto

1. Linha do tempo completa da empresa.
2. Alertas de mudanca cadastral e societaria.
3. Historico de socios antigos, entradas e saidas.
4. Grafo societario entre socios, empresas, grupos, enderecos e contadores.
5. Deteccao de email de contador, escritorio fiscal e contato terceirizado.
6. Score de oportunidade comercial.
7. Eventos de timing comercial.
8. ICP vivo que aprende com respostas, reunioes e conversoes.
9. Listas limpas automaticamente.
10. Cadencias integradas ao dado publico, ICP e timing.
11. CRM automatico de leads quentes.
12. API AI-first com `llms.txt`, OpenAPI e exemplos para agentes.
13. Explicacao "por que esse lead?".
14. Monitoramento de mercado por segmento, CNAE, cidade e UF.
15. Comparacao com clientes atuais para descobrir padroes reais de ICP.
16. Radar de concorrentes, clientes e contas-alvo.
17. Qualidade de dados transparente por fonte, data e confianca.
18. Historico mensal como produto premium.

## Proximas fases recomendadas

1. Criar migrations SQL reais do `receita_staging`.
2. Implementar job Python de carga Postgres com progresso de download e COPY.
3. Validar importacao completa do snapshot mais recente.
4. Criar modelo de diff mensal da Receita.
5. Criar schema operacional inicial em NestJS/Prisma.
6. Migrar busca de empresas para Postgres.
7. Renomear sequencias para cadencias.
8. Criar dicionario completo do banco.
9. Criar documentacao de API publica e `llms.txt`.
10. Criar guia de interface premium para Next.js e super admin.

