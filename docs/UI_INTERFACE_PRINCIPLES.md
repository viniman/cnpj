# Princípios de interface

Este documento define o norte de UX/UI para as próximas interfaces do Radar
CNPJ. Ele vale para o futuro produto em Next.js e também para a limpeza gradual
do super admin Python.

## Princípios gerais

- A interface deve parecer uma ferramenta B2B premium, densa, clara e operável
  por times comerciais, growth, dados e operações.
- O produto deve priorizar busca, comparação, filtros, listas, alertas,
  cadências e decisões acionáveis.
- A experiência deve evitar telas gigantes que misturam responsabilidades
  diferentes.
- Cada página deve ter uma tarefa principal evidente.
- Dados sensíveis de operação, billing, API e ETL devem ficar separados por
  permissão e contexto.

## Produto cliente

O produto cliente deve ser organizado em áreas como:

- Busca de empresas;
- Listas e segmentos;
- ICP e oportunidades;
- Cadências;
- CRM e respostas;
- Alertas de mudanças;
- Relatórios e métricas;
- API e billing;
- Configurações do workspace.

## Super admin

O super admin deve focar em:

- status da fonte Receita;
- snapshots disponíveis;
- progresso de download;
- progresso de importação;
- saúde do staging;
- jobs, erros e retomadas;
- qualidade dos dados importados;
- auditoria operacional;
- controles internos.

O super admin não precisa ser bonito por vaidade, mas precisa ser claro,
confiável e rápido de operar.

## Regras de experiência

- Filtros devem ser visíveis, combináveis e salváveis.
- Tabelas devem ser densas, com colunas relevantes, ordenação e estados claros.
- Detalhes de empresa devem mostrar origem, snapshot e confiança dos dados.
- Ações perigosas devem ter confirmação e trilha de auditoria.
- O usuário não deve precisar saber IDs internos para enriquecer, listar ou
  operar empresas.
- Mudanças históricas devem aparecer como linha do tempo, não apenas como
  campos sobrescritos.
- Explicações de score devem ser legíveis por humano e por API.
- Cadências devem ser apresentadas como fluxos comerciais, não como logs
  técnicos.

## Design visual

- Aparência profissional, moderna e contida.
- Densidade de informação alta, mas com hierarquia clara.
- Navegação lateral ou superior previsível.
- Cards apenas quando representarem itens ou resumos reais.
- Evitar telas de comando enormes como destino final.
- Usar estados vazios, carregamento, erro e sucesso com mensagens objetivas.
- Priorizar performance percebida em buscas, filtros e listas grandes.
