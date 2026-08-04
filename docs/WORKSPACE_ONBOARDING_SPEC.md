# Fase 28 - Wizard de onboarding operacional

## Objetivo

Criar um fluxo local que deixe uma nova empresa interna operacional em poucos
minutos: workspace, perfil, playbook aplicado, ICP inicial, template de copy,
cadencia semi-supervisionada e OKR inicial. O wizard deve reutilizar os
trilhos ja existentes, sem criar atalhos que contornem auditoria ou aprovacao
humana.

## Escopo

- Criar servico `run_workspace_onboarding`.
- Criar workspace e tornar esse workspace o contexto ativo.
- Preencher perfil operacional com nome, vertical, tom, dominio de envio,
  remetente e cor.
- Usar playbook default do novo workspace ou clone de playbook existente.
- Aplicar o playbook escolhido ao workspace.
- Criar ICP inicial a partir do payload ou do conteudo do playbook.
- Criar template de primeiro contato com rodape de compliance do backend.
- Criar cadencia inicial semi-supervisionada com aprovacao humana.
- Criar OKR inicial com KR rastreavel por `kpi_key`.
- Registrar auditoria e resumo da execucao.
- Expor endpoint local e painel simples no Command Center.

## Fora do escopo desta fase

- Envio real de e-mail.
- Criacao automatica de leads ou inscricao de listas em cadencia.
- Fluxo multiusuario/RBAC.
- Wizard em etapas persistidas com progresso parcial.
- Validacao DNS real de dominio de envio.

## Decisao central

Onboarding e composicao de servicos existentes, nao um caminho paralelo. O
wizard chama as mesmas funcoes de playbook, ICP, template, cadencia e OKR,
mantendo contexto ativo, auditoria e aprovacao humana por passo.

## Implementado nesta fase

- Tabela `workspace_onboarding_runs` para registrar resumo do wizard.
- Servico `run_workspace_onboarding`.
- Endpoint `POST /api/workspaces/onboarding`.
- Criacao de workspace e troca automatica para o novo contexto ativo.
- Aplicacao de playbook default ou clone de playbook de origem.
- Criacao de ICP inicial a partir do payload ou do playbook.
- Criacao de template inicial com rodape de compliance preservado pelo backend.
- Criacao de cadencia inicial com aprovacao humana obrigatoria nos passos.
- Criacao de OKR inicial com KR ligado a KPI conhecido.
- Painel `Onboarding operacional` no Command Center.
- Testes automatizados cobrindo onboarding default e baseado em playbook clonado.

## Criterios de aceite

- Onboarding cria novo workspace e o torna ativo.
- Perfil operacional recebe dados informados.
- Playbook e aplicado ao workspace criado.
- ICP inicial e criado no workspace novo.
- Template inicial e criado com versao ativa.
- Cadencia inicial usa o template criado e exige aprovacao humana.
- OKR inicial e criado com KR rastreavel.
- Reuso de playbook clonado e opcional e auditavel.
- Testes automatizados provam que tudo fica no novo workspace.
