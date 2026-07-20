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

## Proximas fases sugeridas

1. PostgreSQL com `pg_trgm` e `unaccent`.
2. Importador oficial escalavel com staging e checkpoints.
3. Autenticacao real e RBAC.
4. Filtros salvos e tags no frontend.
5. Canal de solicitacao de titular.
6. Motor de score configuravel por workspace.
7. Integracao futura com provedores de email somente com opt-out, bounce e limites.
