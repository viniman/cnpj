# Principios de interface

Este documento define o norte de UX/UI para as proximas interfaces do Radar
CNPJ. Ele vale para o futuro produto em Next.js e tambem para a limpeza gradual
do super admin Python.

## Principios gerais

- A interface deve parecer uma ferramenta B2B premium, densa, clara e operavel
  por times comerciais, growth, dados e operacoes.
- O produto deve priorizar busca, comparacao, filtros, listas, alertas,
  cadencias e decisoes acionaveis.
- A experiencia deve evitar telas gigantes que misturam responsabilidades
  diferentes.
- Cada pagina deve ter uma tarefa principal evidente.
- Dados sensiveis de operacao, billing, API e ETL devem ficar separados por
  permissao e contexto.

## Produto cliente

O produto cliente deve ser organizado em areas como:

- Busca de empresas;
- Listas e segmentos;
- ICP e oportunidades;
- Cadencias;
- CRM e respostas;
- Alertas de mudancas;
- Relatorios e metricas;
- API e billing;
- Configuracoes do workspace.

## Super admin

O super admin deve focar em:

- status da fonte Receita;
- snapshots disponiveis;
- progresso de download;
- progresso de importacao;
- saude do staging;
- jobs, erros e retomadas;
- qualidade dos dados importados;
- auditoria operacional;
- controles internos.

O super admin nao precisa ser bonito por vaidade, mas precisa ser claro,
confiavel e rapido de operar.

## Regras de experiencia

- Filtros devem ser visiveis, combinaveis e salvaveis.
- Tabelas devem ser densas, com colunas relevantes, ordenacao e estados claros.
- Detalhes de empresa devem mostrar origem, snapshot e confianca dos dados.
- Acoes perigosas devem ter confirmacao e trilha de auditoria.
- O usuario nao deve precisar saber IDs internos para enriquecer, listar ou
  operar empresas.
- Mudancas historicas devem aparecer como linha do tempo, nao apenas como
  campos sobrescritos.
- Explicacoes de score devem ser legiveis por humano e por API.
- Cadencias devem ser apresentadas como fluxos comerciais, nao como logs
  tecnicos.

## Design visual

- Aparencia profissional, moderna e contida.
- Densidade de informacao alta, mas com hierarquia clara.
- Navegacao lateral ou superior previsivel.
- Cards apenas quando representarem itens ou resumos reais.
- Evitar telas de comando enormes como destino final.
- Usar estados vazios, carregamento, erro e sucesso com mensagens objetivas.
- Priorizar performance percebida em buscas, filtros e listas grandes.

