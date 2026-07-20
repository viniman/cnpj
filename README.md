# Radar CNPJ Interno

MVP local para pesquisar, filtrar, qualificar e exportar dados publicos de CNPJ com foco em prospeccao B2B responsavel.

O projeto foi montado para uso interno em localhost. Ele ja inclui dashboard, busca de empresas, detalhe com socios, listas, higiene de email, supressao, exportacao CSV/XLSX e auditoria.

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
- `GET /api/companies`
- `GET /api/companies/{id}`
- `POST /api/import`
- `POST /api/seed`
- `GET /api/sources/official`
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

## Proximas fases sugeridas

1. PostgreSQL com `pg_trgm` e `unaccent`.
2. Importador oficial escalavel com staging e checkpoints.
3. Autenticacao real e RBAC.
4. Filtros salvos e tags no frontend.
5. Canal de solicitacao de titular.
6. Motor de score configuravel por workspace.
7. Descoberta assistida de dominio oficial com validacao de identidade.
8. ICP estruturado e priorizacao automatizada para fila SDR.
9. Classificacao de respostas, handoff humano e reunioes.
10. Integracao futura com provedores de email somente com opt-out, bounce e limites.
