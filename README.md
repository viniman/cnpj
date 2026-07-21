# Radar CNPJ Interno

MVP local para pesquisar, filtrar, qualificar e exportar dados publicos de CNPJ com foco em prospeccao B2B responsavel.

O projeto foi montado para uso interno em localhost. Ele ja inclui dashboard, busca de empresas, detalhe com socios, listas, higiene de email, supressao, exportacao CSV/XLSX e auditoria.

## Centro de Comando

A aba `Comando` agrega a operacao em uma tela unica:

- Metricas de aprovacoes, handoffs, reunioes abertas, leads ativos e acoes.
- Inbox humano com itens vindos de `approval_queue`, `handoffs` e `meetings`.
- CRM Kanban por estado do lead e da jornada.
- Feed de atividade baseado em `agent_actions`, sempre com origem e motivo.
- Replay por lead, com timeline auditavel de priorizacao, aprovacao, envio,
  resposta, handoff, reuniao, conversao e acoes do agente.
- OKRs e KPIs com formula explicita, calculados a partir do funil real.
- Playbooks reutilizaveis com ICP, copy, cadencia, OKR e governanca em pacote
  versionado.
- Governanca do agente com versoes de configuracao, staging, ativacao,
  simulacoes locais e custo estimado de IA.
- Notificacoes proativas para lead quente, campanha pausada e OKR atingido ou
  em risco.
- Comparacao executiva multi-workspace com perfis de empresa e snapshots.

Endpoint:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/command-center"
```

Aplicar uma decisao da inbox:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/command-center/actions" `
  -Body '{"source_type":"approval","source_id":1,"decision":"approve","note":"Aprovado pelo Command Center"}' `
  -ContentType "application/json"
```

Importante: o Command Center nao cria uma fonte paralela de verdade. Ele mostra
os dados agregados e preserva `source_type` e `source_id` para a acao continuar
no modulo de origem. As decisoes da inbox sao roteadas para esses mesmos
modulos.

Consultar replay de um lead:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/leads/1/timeline"
```

Consultar OKRs e KPIs:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/okrs"
```

Consultar governanca do agente:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/agent-governance"
```

Criar uma nova configuracao em staging:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/agent-governance/configs" `
  -Body '{"name":"SDR conservador","model_name":"gpt-5-mini","prompt_text":"Priorize ICP e escale duvidas.","rules":{"requires_human_approval":true}}' `
  -ContentType "application/json"
```

Consultar biblioteca de playbooks:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/playbooks"
```

Criar playbook:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/playbooks" `
  -Body '{"name":"Outbound B2B Servicos Locais","description":"Pacote inicial","content":{"icp":{"states":["SP"],"target_cnaes":["620"],"min_email_score":30},"copy":{"tone":"direto, B2B, consultivo"},"cadence":{"steps":[{"name":"Primeiro contato","wait_days":0}]},"okr":{"objective":"Validar nicho","key_results":[{"kpi_key":"replies_received","target_value":10}]},"governance":{"requires_human_approval":true}}}' `
  -ContentType "application/json"
```

Clonar playbook para outro workspace:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/playbooks/1/clone" `
  -Body '{"target_org_id":2,"name":"Clone para Nine","description":"Teste controlado de playbook vencedor"}' `
  -ContentType "application/json"
```

Criar plano de execucao revisavel para um playbook:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/playbooks/1/execution-plans" `
  -Body '{"version_id":1,"apply_note":"Validar antes de criar ICP, template, sequencia e OKR"}' `
  -ContentType "application/json"
```

Consultar e aplicar planos de execucao:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/playbook-execution-plans"

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/playbook-execution-plans/1/apply" `
  -Body '{"note":"Aplicado apos revisao operacional"}' `
  -ContentType "application/json"
```

Gerar notificacoes proativas locais:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/notifications/generate" `
  -Body '{}' `
  -ContentType "application/json"
```

Consultar notificacoes:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/notifications"
```

Consultar comparacao executiva de workspaces:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/workspaces/comparison"
```

Consultar fundacao SaaS local:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/saas/account"
```

Aplicar um plano SaaS local ao workspace ativo:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/saas/plan-subscription" `
  -Body '{"plan_code":"starter","billing_period":"monthly","note":"Validar plano Starter"}' `
  -ContentType "application/json"
```

Criar chave de API e ajustar creditos:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/saas/api-keys" `
  -Body '{"name":"Integracao interna","scopes":["companies:read","emails:read","exports:create"]}' `
  -ContentType "application/json"

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/saas/credits/adjust" `
  -Body '{"amount":100,"reason":"Credito manual inicial"}' `
  -ContentType "application/json"
```

Consultar empresas pela API publica local:

```powershell
$token = "<token retornado na criacao da chave>"
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/public/companies?state=SP&has_email=1&limit=10" `
  -Headers @{"X-API-Key"=$token}
```

Consultar contrato OpenAPI da API publica local:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/public/openapi.json"
```

Consultar e atualizar configuracao de scoring do workspace:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scoring/config"

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/scoring/config" `
  -Body '{"name":"Scoring RH","email_prefix_rules":{"rh":{"area":"decisor de recursos humanos","score":82,"label":"decision_maker"}}}' `
  -ContentType "application/json"
```

Salvar segmento de empresas e converter para ICP:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/saved-filters" `
  -Body '{"name":"Software SP com email","filters":{"state":"SP","cnae":"620","has_email":"1","min_score":"20"}}' `
  -ContentType "application/json"

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/saved-filters"

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/saved-filters/1/icp" `
  -Body '{"name":"ICP Software SP","max_leads":50}' `
  -ContentType "application/json"
```

Criar workspace para comparacao:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/workspaces" `
  -Body '{"name":"Nine","vertical":"servicos locais","default_tone":"direto, acolhedor","sender_name":"Time Nine"}' `
  -ContentType "application/json"
```

Executar onboarding operacional:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/workspaces/onboarding" `
  -Body '{"workspace":{"name":"Nine","vertical":"servicos locais","default_tone":"direto, B2B, consultivo"},"icp":{"criteria":{"states":["SP"],"cnaes":["620"],"min_email_score":30}}}' `
  -ContentType "application/json"
```

## Rodar localmente

Com Python:

```powershell
python -m radar_cnpj.server
```

Depois abra:

```text
http://127.0.0.1:8000
```

Com Docker:

```powershell
docker compose up --build
```

## Primeiro uso

1. Abra `http://127.0.0.1:8000`.
2. Clique em `Carregar amostra`.
3. Va para `Empresas` e filtre por UF, cidade, CNAE, porte, situacao ou email.
4. Crie uma lista em `Listas`.
5. Selecione empresas na busca e adicione na lista.
6. Na lista, informe a finalidade e exporte CSV ou XLSX.
7. Use `Higiene` para validar emails e adicionar supressoes.

## Fonte oficial automatica

A tela `Importacao` agora consegue descobrir a base oficial da Receita sem voce procurar links manualmente.

O sistema usa o compartilhamento publico oficial do SERPRO/Receita:

```text
https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9
```

Pela API interna:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/sources/official"
```

Baixar automaticamente os arquivos pequenos de dominio do ultimo snapshot:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sources/official/sync" `
  -Body '{"mode":"domains"}' `
  -ContentType "application/json"
```

Baixar e importar um chunk oficial limitado:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sources/official/sync" `
  -Body '{"mode":"chunk","snapshot":"2026-06","chunk":1,"limit":1000}' `
  -ContentType "application/json"
```

Retomar automaticamente o mesmo snapshot/chunk a partir do ultimo checkpoint:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sources/official/sync" `
  -Body '{"mode":"chunk","snapshot":"2026-06","chunk":1,"limit":1000,"resume":true}' `
  -ContentType "application/json"
```

Listar checkpoints de importacao oficial:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/sources/official/checkpoints"
```

Atencao: cada chunk oficial pode ter centenas de MB, e a base completa mensal tem varios GB. O MVP suporta descoberta, download e importacao limitada em SQLite. Para a carga nacional completa, use a migracao planejada para PostgreSQL + staging + COPY.

## Consulta por API

Tambem foi adicionada consulta individual via BrasilAPI:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sources/brasilapi/cnpj" `
  -Body '{"cnpj":"00000000000191"}' `
  -ContentType "application/json"
```

A consulta salva a empresa localmente, incluindo socios quando retornados pela API.

## Scoring avancado de e-mail

O modulo de higiene agora tem uma camada extra de score comercial.

Ela considera:

- Prefixo do e-mail (`contato@`, `comercial@`, `ceo@`, `contabil@` etc.).
- Dominio pessoal, corporativo ou descartavel.
- Match entre o local-part do e-mail e nomes de socios/administradores.
- Mesmo e-mail usado em varios CNPJs.
- Mesmo dominio usado em varios CNPJs.
- Lista de supressao e opt-out.

Endpoint:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/emails/score" `
  -Body '{"emails":["ceo@empresa.com.br","contato@empresa.com.br"]}' `
  -ContentType "application/json"
```

Tambem funciona por lista:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/emails/score" `
  -Body '{"list_id":1}' `
  -ContentType "application/json"
```

Os resultados ficam persistidos em:

- `email_classifications`
- `email_score_log`
- `known_shared_domains`

Cada workspace tambem pode ajustar pesos de prefixos na aba `Higiene`, painel
`Config scoring`. A configuracao ativa fica em `workspace_scoring_configs` e e
aplicada por `score_email_record` antes de campanhas, listas e ICPs usarem o
score persistido.

## Score de empresa por workspace

O score base da empresa continua salvo em `companies.opportunity_score`, mas
cada workspace pode criar um overlay proprio em `company_workspace_scores`.
Isso permite ajustar pesos de setor, porte, capital, idade e sinais de contato
sem contaminar outro workspace.

Consultar e atualizar a configuracao:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scoring/company-config"

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/scoring/company-config" `
  -Body '{"name":"Score Saude","rules":{"sector_bonus":{"Saude":30}}}' `
  -ContentType "application/json"
```

Recalcular um lote para o workspace ativo:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/scoring/company-rescore" `
  -Body '{"limit":500}' `
  -ContentType "application/json"
```

A busca de empresas, o detalhe da empresa e a priorizacao ICP usam o overlay do
workspace quando ele existe; caso contrario, continuam usando o score base.
Na UI local, isso fica na aba `Higiene`, painel `Score empresa`.

## Historico e rollback de scoring

As configuracoes de score de e-mail e de empresa agora mantem historico em
`workspace_score_config_versions`. Cada alteracao cria uma nova versao ativa e
arquiva a anterior. Rollback tambem cria nova versao ativa, preservando quando
a restauracao aconteceu.

Listar versoes:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scoring/config-versions"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scoring/config-versions?type=email"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scoring/config-versions?type=company"
```

Comparar a versao ativa atual com uma versao historica antes de restaurar:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scoring/config-versions/1/diff"
```

Restaurar uma versao:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/scoring/config-versions/1/rollback" `
  -Body '{"change_note":"Rollback operacional"}' `
  -ContentType "application/json"
```

Na UI local, use `Higiene`, painel `Historico scoring`. O botao `Diff` mostra
campos alterados antes do rollback. Para score de empresa, apos rollback, use
`Recalcular empresas` para atualizar o overlay ja calculado.

## Enriquecimento de empresas

A aba `Enriquecimento` permite coletar sinais publicos do site de uma empresa
sem sobrescrever os dados oficiais do CNPJ.

Ela extrai:

- E-mails publicados.
- Telefones e WhatsApp em formatos comuns.
- Links sociais institucionais.
- Tecnologias do site, como WordPress, Shopify, Nuvemshop, Google Tag Manager,
  Google Analytics, RD Station, Hotjar, Intercom, Zendesk e Cloudflare.
- Score de maturidade digital com explicacao.

Processar HTML informado localmente:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/enrichment/company" `
  -Body '{"company_id":1,"source_url":"https://empresa.com.br","html":"<html>contato@empresa.com.br</html>"}' `
  -ContentType "application/json"
```

Coletar uma URL explicita com `robots.txt` e cache:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/enrichment/company" `
  -Body '{"company_id":1,"url":"https://empresa.com.br","ttl_days":30}' `
  -ContentType "application/json"
```

Buscar o ultimo enriquecimento salvo:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/enrichment/company/1"
```

Os dados ficam separados do cadastro oficial em:

- `company_enrichment`
- `scraping_jobs`
- `scraping_cache`

## Experimentos comerciais simulados

A aba `Experimentos` cria um mini-CRM local para testar qualidade de lista,
copy e funil antes de qualquer envio real.

Fluxo:

1. Crie uma lista na aba `Listas`.
2. Va para `Experimentos`.
3. Selecione a lista e clique em `Criar leads`.
4. Crie uma campanha simulada.
5. Clique em `Simular` na campanha.
6. Registre eventos manuais de funil quando quiser testar clique, resposta,
   conversao, bounce ou complaint.

Criar leads a partir de lista:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/experiments/leads/from-list" `
  -Body '{"list_id":1}' `
  -ContentType "application/json"
```

Criar campanha simulada:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/experiments/campaigns" `
  -Body '{"name":"Teste SP","niche":"Software SP","subject":"Ideia rapida","body":"Mensagem direta","cta_url":"https://usevagou.com.br/contato"}' `
  -ContentType "application/json"
```

Simular a campanha:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/experiments/campaigns/1/simulate" `
  -Body '{"list_id":1,"limit":50}' `
  -ContentType "application/json"
```

Registrar evento manual:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/experiments/events" `
  -Body '{"send_id":1,"event_type":"clicked"}' `
  -ContentType "application/json"
```

Tabelas principais:

- `leads`
- `campaigns`
- `campaign_variants`
- `sends`
- `events`
- `conversions`
- `throttle_config`
- `pause_events`

Importante: esta fase nao envia e-mail. O provider e sempre `simulated`.

## Templates de e-mail versionados

A aba `Templates` permite criar copies reutilizaveis com variaveis e preview
com dados reais de empresa. O rodape de compliance e sempre injetado pelo
backend e nao fica editavel no corpo do template.

Variaveis principais:

- `{{nome_empresa}}`
- `{{razao_social}}`
- `{{cidade}}`
- `{{estado}}`
- `{{cnae_descricao}}`
- `{{setor}}`
- `{{segmento}}`
- `{{nome_contato}}`
- `{{motivo_contato}}`
- `{{cta_url}}`

Criar template:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/templates" `
  -Body '{"name":"Primeiro contato","purpose":"first_contact","subject":"Ideia para {{nome_empresa}}","body":"Vi que a {{nome_empresa}} {{motivo_contato}}. CTA: {{cta_url}}"}' `
  -ContentType "application/json"
```

Criar nova versao:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/templates/1/versions" `
  -Body '{"subject":"Nova ideia para {{nome_empresa}}","body":"Ola {{nome_contato}}, podemos conversar sobre {{cidade}}?"}' `
  -ContentType "application/json"
```

Renderizar preview:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/templates/render" `
  -Body '{"template_id":1,"company_id":1,"cta_url":"https://usevagou.com.br/contato"}' `
  -ContentType "application/json"
```

Tabelas:

- `email_templates`
- `email_template_versions`

## Sequencias semi-supervisionadas

A aba `Sequencias` cria cadencias multi-step usando templates versionados, mas
mantem aprovacao humana antes de qualquer execucao. Esta fase ainda nao envia
e-mail real: aprovacoes criam envios simulados e registros de auditoria.

Fluxo:

1. Crie uma lista com empresas elegiveis.
2. Crie um template de primeiro contato e, opcionalmente, um follow-up.
3. Va para `Sequencias`.
4. Crie uma sequencia com os templates.
5. Inscreva a lista na sequencia.
6. Revise cada item em `Aprovacoes pendentes`.
7. Aprove ou rejeite com uma nota de decisao.
8. Quando uma jornada ficar em espera, prepare o proximo passo.

Criar sequencia:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sequences" `
  -Body '{"name":"Cadencia inicial","steps":[{"name":"Primeiro contato","template_id":1,"wait_days":0},{"name":"Follow-up","template_id":2,"wait_days":3}]}' `
  -ContentType "application/json"
```

Inscrever lista:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sequences/1/enroll" `
  -Body '{"list_id":1}' `
  -ContentType "application/json"
```

Aprovar um passo:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/approvals/1/approve" `
  -Body '{"note":"Aprovado para teste local"}' `
  -ContentType "application/json"
```

Preparar proximo passo de uma jornada:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sequences/journeys/1/prepare-next" `
  -Body '{}' `
  -ContentType "application/json"
```

Tabelas:

- `sequences`
- `sequence_steps`
- `lead_journey`
- `approval_queue`
- `agent_actions`

## ICP estruturado e fila SDR

A aba `ICP SDR` permite transformar filtros comerciais em regra estruturada.
O agente futuro so pode priorizar empresas que passem por essa regra no
backend.

Fluxo:

1. Crie ou escolha uma lista de empresas.
2. Abra `ICP SDR`.
3. Crie um ICP com UF, cidade, CNAE, setor, porte e scores minimos.
4. Clique em `Priorizar` na regra ICP.
5. Revise a `Fila SDR priorizada`.
6. Aceite ou rejeite cada sugestao com uma nota.

Criar ICP:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/icp-rules" `
  -Body '{"name":"Software SP","criteria":{"states":["SP"],"cnaes":["620"],"min_email_score":30,"max_leads":50}}' `
  -ContentType "application/json"
```

Priorizar uma lista:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/icp-rules/1/prioritize" `
  -Body '{"list_id":1}' `
  -ContentType "application/json"
```

Aceitar sugestao:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/priority-queue/1/accept" `
  -Body '{"note":"Bom fit para cadencia"}' `
  -ContentType "application/json"
```

Tabelas:

- `icp_rules`
- `lead_priority_queue`

## Segmentos salvos

A aba `Empresas` permite salvar a combinacao atual de filtros como segmento do
workspace ativo. O segmento guarda uma fotografia normalizada dos filtros e a
contagem de empresas no momento da criacao, mas continua reaplicando a busca
dinamicamente quando usado.

Fluxo:

1. Filtre por nome, UF, cidade, CNAE, setor, porte, situacao, email, telefone
   ou score minimo.
2. Informe um nome em `Segmentos salvos e ICP`.
3. Clique em `Salvar filtros atuais`.
4. Reaplique o segmento quando quiser refazer a busca.
5. Crie um ICP a partir do segmento para alimentar a fila SDR.

Tabelas:

- `saved_filters`
- `icp_rules`

## Respostas e handoff humano

A aba `Respostas` permite simular uma resposta recebida e classificar a
intencao em categorias fixas. O conteudo da resposta e tratado como dado
externo, nunca como instrucao para o sistema.

Fluxo:

1. Informe `send_id`, `lead_id` ou e-mail.
2. Cole assunto/corpo da resposta.
3. Clique em `Classificar resposta`.
4. Revise a classificacao e os handoffs pendentes.
5. Resolva ou dispense o handoff com uma nota.

Classificar resposta:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/replies/classify" `
  -Body '{"send_id":1,"body":"Tenho interesse, podemos conversar esta semana?"}' `
  -ContentType "application/json"
```

Resolver handoff:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/handoffs/1/resolve" `
  -Body '{"note":"Respondido manualmente"}' `
  -ContentType "application/json"
```

Categorias:

- `interest_meeting`
- `question`
- `not_interested`
- `opt_out`
- `out_of_office`
- `wrong_person`
- `ambiguous`

Tabelas:

- `reply_classifications`
- `handoffs`

## Reunioes e agenda operacional

A aba `Respostas` tambem permite transformar um handoff em reuniao registrada.
Esta fase nao envia convite nem integra calendario; ela cria um registro
operacional auditavel para o humano conduzir a proxima acao.

Fluxo:

1. Classifique uma resposta de interesse.
2. Clique em `Reuniao` no handoff pendente.
3. Informe horario, link, responsavel e nota.
4. Crie a reuniao por handoff.
5. Atualize o status para `completed`, `cancelled` ou `no_show`.

Criar reuniao por handoff:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/handoffs/1/meeting" `
  -Body '{"scheduled_at":"2026-07-21T14:00","meeting_url":"https://meet.example.com/demo","notes":"Horario combinado por resposta"}' `
  -ContentType "application/json"
```

Criar reuniao manual por lead:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/meetings" `
  -Body '{"lead_id":1,"scheduled_at":"2026-07-21T14:00","notes":"Contato feito manualmente"}' `
  -ContentType "application/json"
```

Atualizar status:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/meetings/1/status" `
  -Body '{"status":"completed","note":"Reuniao feita; lead qualificado"}' `
  -ContentType "application/json"
```

Tabelas:

- `meetings`

## Importar CSV simplificado

Na tela `Importacao`, informe o caminho local de um CSV com algumas destas colunas:

```text
cnpj, legal_name, trade_name, status, opening_date, main_cnae_code,
main_cnae_description, secondary_cnaes, legal_nature, size,
establishment_type, street, number, complement, district, city, state,
zip_code, email, phone, capital_social, partners, source_name,
source_url, legal_basis
```

Tambem sao aceitos nomes em portugues como `razao_social`, `nome_fantasia`, `situacao`, `cidade`, `uf`, `telefone`, `socios`.

O campo `partners` pode usar:

```text
Nome do socio|Qualificacao|Data de entrada;Outro socio|Qualificacao|Data
```

## Importar amostra Receita

O MVP tambem aceita um diretorio pequeno com arquivos no padrao Receita:

- `EMPRECSV`
- `ESTABELE`
- `SOCIOCSV` opcional
- `CNAECSV` opcional
- `MUNICCSV` opcional

Use isso para amostras. A base nacional completa deve ser processada com PostgreSQL, tabelas de staging e `COPY`.

## Endpoints principais

- `GET /api/dashboard`
- `GET /api/command-center`
- `POST /api/command-center/actions`
- `GET /api/leads/{id}/timeline`
- `GET /api/okrs`
- `POST /api/okrs`
- `GET /api/agent-governance`
- `POST /api/agent-governance/configs`
- `POST /api/agent-governance/configs/{id}/activate`
- `POST /api/agent-governance/simulations`
- `POST /api/agent-governance/costs`
- `GET /api/playbooks`
- `POST /api/playbooks`
- `POST /api/playbooks/{id}/versions`
- `POST /api/playbooks/{id}/apply`
- `POST /api/playbooks/{id}/clone`
- `GET /api/playbook-execution-plans`
- `POST /api/playbooks/{id}/execution-plans`
- `POST /api/playbook-execution-plans/{id}/apply`
- `GET /api/saas/account`
- `POST /api/saas/api-keys`
- `POST /api/saas/api-keys/{id}/revoke`
- `POST /api/saas/credits/adjust`
- `GET /api/public/companies`
- `GET /api/public/openapi.json`
- `GET /api/scoring/config`
- `POST /api/scoring/config`
- `GET /api/scoring/company-config`
- `POST /api/scoring/company-config`
- `POST /api/scoring/company-rescore`
- `GET /api/scoring/config-versions`
- `GET /api/scoring/config-versions/{id}/diff`
- `POST /api/scoring/config-versions/{id}/rollback`
- `GET /api/saved-filters`
- `POST /api/saved-filters`
- `POST /api/saved-filters/{id}/icp`
- `GET /api/notifications`
- `POST /api/notifications/generate`
- `POST /api/notifications/{id}/mark-read`
- `POST /api/notifications/{id}/dismiss`
- `GET /api/workspace-context`
- `POST /api/workspace-context`
- `GET /api/workspaces/comparison`
- `POST /api/workspaces`
- `POST /api/workspaces/onboarding`
- `POST /api/workspaces/{id}/snapshot`
- `GET /api/companies`
- `GET /api/companies/{id}`
- `POST /api/import`
- `POST /api/seed`
- `GET /api/sources/official`
- `GET /api/sources/official/checkpoints`
- `POST /api/sources/official/sync`
- `POST /api/sources/official/download`
- `POST /api/sources/brasilapi/cnpj`
- `GET /api/lists`
- `POST /api/lists`
- `POST /api/lists/{id}/companies`
- `GET /api/lists/{id}/export?format=csv&purpose=...`
- `POST /api/emails/validate`
- `POST /api/emails/score`
- `POST /api/enrichment/company`
- `GET /api/enrichment/company/{company_id}`
- `POST /api/experiments/leads/from-list`
- `GET /api/experiments/leads`
- `POST /api/experiments/campaigns`
- `GET /api/experiments/campaigns`
- `GET /api/experiments/campaigns/{id}`
- `POST /api/experiments/campaigns/{id}/simulate`
- `POST /api/experiments/events`
- `POST /api/templates`
- `GET /api/templates`
- `GET /api/templates/{id}`
- `POST /api/templates/{id}/versions`
- `POST /api/templates/render`
- `POST /api/sequences`
- `GET /api/sequences`
- `GET /api/sequences/{id}`
- `POST /api/sequences/{id}/enroll`
- `GET /api/sequences/journeys`
- `POST /api/sequences/journeys/{id}/prepare-next`
- `GET /api/approvals`
- `POST /api/approvals/{id}/approve`
- `POST /api/approvals/{id}/reject`
- `GET /api/agent-actions`
- `POST /api/icp-rules`
- `GET /api/icp-rules`
- `GET /api/icp-rules/{id}`
- `POST /api/icp-rules/{id}/prioritize`
- `GET /api/priority-queue`
- `POST /api/priority-queue/{id}/accept`
- `POST /api/priority-queue/{id}/reject`
- `POST /api/replies/classify`
- `GET /api/replies`
- `GET /api/handoffs`
- `POST /api/handoffs/{id}/resolve`
- `POST /api/handoffs/{id}/dismiss`
- `POST /api/handoffs/{id}/meeting`
- `GET /api/meetings`
- `POST /api/meetings`
- `POST /api/meetings/{id}/status`
- `POST /api/suppression`
- `GET /api/audit`

## Testes

```powershell
python -m unittest discover -s tests
```

## Observacoes importantes

- Esta versao nao dispara email. Ela prepara listas auditaveis.
- Exportacoes exigem finalidade declarada.
- Emails em opt-out/supressao recebem classificacao restritiva.
- Nao armazene CPF completo de socios.
- Nao use scraping agressivo em servicos publicos. Priorize os arquivos oficiais baixaveis.
- Enriquecimento por site e sinal complementar; nao substitui dado oficial da Receita.
- Campanhas locais sao simuladas e nao chamam provedor externo.
- Rodape de compliance de templates e injetado pelo backend.
- Sequencias exigem aprovacao humana por passo antes de simular envio.
- Fila SDR so inclui empresas que passam pelo ICP estruturado no backend.
- Opt-out detectado em resposta vira supressao imediata.
- Respostas ambiguas ou quentes viram handoff humano.
- Reunioes exigem acao humana e respeitam opt-out/supressao.
- Replay por lead e uma composicao de leitura; ele nao substitui as tabelas
  originais nem altera regras de origem.
- Key Results apontam para KPIs calculados; o valor atual nao e salvo como
  verdade paralela.
- Configuracoes do agente passam por staging antes de ativar; simulacoes locais
  nao chamam modelo externo.
- Custos de IA ficam registrados por operacao/modelo/versao para auditoria.
- Aplicar playbook grava uma referencia ativa do workspace; nao sobrescreve ICP,
  sequencias, OKRs ou configuracoes do agente automaticamente.
- Notificacoes guardam origem (`source_type` e `source_id`) e nao alteram o
  registro operacional original ao serem lidas ou dispensadas.
- Comparacao multi-workspace usa metricas por `org_id` onde ja existe esse
  vinculo; empresas sao contadas pelas listas do workspace ate a futura
  migracao completa da base bruta.
- A topbar permite trocar o workspace operacional ativo. Nesta fase, dashboard,
  listas, notificacoes e OKRs ja respeitam esse contexto; os demais dominios
  seguem em migracao gradual.
- Experimentos/campanhas simuladas tambem respeitam o workspace ativo: leads,
  campanhas, simulacoes, eventos e funil sao filtrados por contexto.
- Templates de e-mail tambem respeitam o workspace ativo: criacao, listagem,
  versoes e renderizacao nao atravessam workspaces.
- Sequencias, jornadas, aprovacoes humanas e acoes de cadencia tambem usam o
  workspace ativo; IDs de outro workspace sao recusados pelo backend.
- ICP estruturado e fila SDR tambem usam o workspace ativo; regras, listas e
  sugestoes de outro workspace sao recusadas pelo backend.
- Respostas, handoffs e reunioes tambem usam o workspace ativo; leads, envios,
  handoffs e reunioes de outro workspace sao recusados pelo backend.
- Command Center e replay por lead tambem usam o workspace ativo; metricas,
  inbox, Kanban, atividade e timeline seguem a empresa selecionada na topbar.
- Governanca do agente e custos de IA tambem usam o workspace ativo; cada
  empresa tem configuracao ativa, simulacoes e custos proprios.
- Playbooks tambem usam o workspace ativo; biblioteca, versoes, perfil
  operacional e aplicacao ativa nao atravessam empresas selecionadas na topbar.
- Clonar playbook entre workspaces cria uma copia independente e auditavel no
  destino; nao aplica automaticamente ICP, cadencia, OKR ou governanca.
- Planos de execucao de playbook criam uma previa auditavel antes de
  materializar ICP, template, sequencia e OKR; apenas a acao explicita de
  aplicar o plano cria esses artefatos.
- A fundacao SaaS tambem usa o workspace ativo: chaves de API, carteira e
  ledger de creditos nao atravessam empresas. Token completo aparece apenas na
  criacao; depois so prefixo/mascara ficam disponiveis.
- A API publica local usa a organizacao da chave, aplica escopo, rate limit e
  saldo antes de consultar empresas, e registra usos aceitos/bloqueados.
- O onboarding operacional cria uma nova empresa pronta para revisao no Command
  Center: workspace, playbook aplicado, ICP, template, sequencia, OKR e default
  de agente, sem envio real.
- Auditoria operacional tambem usa o workspace ativo; `/api/audit` mostra os
  eventos da empresa selecionada na topbar.
- Configuracao de scoring tambem usa o workspace ativo; pesos de prefixo como
  `rh@`, `financeiro@` ou `comercial@` podem mudar por empresa interna sem
  alterar o algoritmo puro.
- Score de empresa tambem usa o workspace ativo; `company_workspace_scores`
  funciona como overlay por empresa/workspace e nao sobrescreve
  `companies.opportunity_score`.
- Historico de scoring tambem usa o workspace ativo; rollback cria nova versao
  ativa em `workspace_score_config_versions`, mantendo a linha do tempo
  auditavel.
- Diff de scoring tambem usa o workspace ativo e compara snapshots ja
  versionados; ele nao cria estado paralelo nem altera configuracoes.
- Segmentos salvos tambem usam o workspace ativo; filtros normalizados ficam em
  `saved_filters`, podem ser reaplicados na busca e podem gerar `icp_rules`
  preservando os filtros originais em `criteria.source_filters`.
- Importacao oficial usa checkpoints globais por `snapshot + chunk`; `resume`
  retoma do `next_offset` salvo sem o operador procurar manualmente onde parou.

## Proximas fases sugeridas

1. PostgreSQL com `pg_trgm` e `unaccent`.
2. Staging PostgreSQL e `COPY` para carga nacional completa.
3. Autenticacao real e RBAC.
4. Tags operacionais no frontend.
5. Canal de solicitacao de titular.
6. Simulacao estatistica de impacto antes/depois das configuracoes de score.
7. Descoberta assistida de dominio oficial com validacao de identidade.
8. Templates de resposta manual assistida.
9. Troca de contexto operacional por workspace.
10. Adaptadores reais de notificacao: Slack, WhatsApp e resumo por e-mail.
11. Integracao futura com provedores de email somente com opt-out, bounce e limites.
