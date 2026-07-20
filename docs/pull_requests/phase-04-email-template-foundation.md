# PR local - Fase 04: Email template foundation

Branch: `feature/04-email-template-foundation`

Base local: `master`

## Objetivo

Criar uma biblioteca de templates de e-mail reutilizaveis, versionados e
renderizados no backend, com rodape de compliance obrigatorio.

## Implementado

- Especificacao da fase em `docs/EMAIL_TEMPLATE_SPEC.md`.
- ADR-006 definindo rodape de compliance injetado pelo backend.
- Tabelas:
  - `email_templates`
  - `email_template_versions`
- Modulo `radar_cnpj/email_templates.py`:
  - extracao de variaveis
  - validacao de variaveis de sistema
  - contexto de empresa
  - renderizacao de assunto/corpo
  - rodape de compliance obrigatorio
- Servicos:
  - criar template
  - criar nova versao
  - listar templates
  - buscar template
  - renderizar preview
- API:
  - `POST /api/templates`
  - `GET /api/templates`
  - `GET /api/templates/{id}`
  - `POST /api/templates/{id}/versions`
  - `POST /api/templates/render`
- UI:
  - nova aba `Templates`
  - editor de assunto/corpo
  - criacao de nova versao
  - preview com empresa real
  - aplicar template renderizado no formulario de campanha simulada

## Checklist de aceite

- [x] Criar template gera versao 1 ativa.
- [x] Criar nova versao nao sobrescreve versao anterior.
- [x] Renderizacao substitui variaveis conhecidas com dado real da empresa.
- [x] Variaveis desconhecidas aparecem em `missing_variables`.
- [x] Rodape de compliance e sempre injetado no corpo renderizado.
- [x] Usuario nao consegue salvar `{{unsubscribe_url}}` ou `{{privacy_url}}`
  no corpo editavel.
- [x] Testes automatizados cobrem criacao, versionamento, renderizacao e
  rodape.
- [x] Smoke test HTTP cria template, cria versao 2 e renderiza com rodape
  injetado.

## Como testar localmente

```powershell
python -m unittest discover -s tests
```

Resultado esperado:

```text
Ran 24 tests
OK
```

Teste manual sugerido:

```powershell
python -m radar_cnpj.server
```

1. Abra `http://127.0.0.1:8000`.
2. Carregue a amostra.
3. Abra `Templates`.
4. Crie um template com `{{nome_empresa}}`, `{{motivo_contato}}` e
   `{{cta_url}}`.
5. Informe um ID de empresa e clique em `Renderizar`.
6. Use `Usar na campanha` para preencher uma campanha simulada.

## Observacoes

- Nao ha remoto Git configurado, entao este PR esta documentado localmente.
- O rodape nao fica salvo no corpo editavel; ele entra apenas na renderizacao.
- Envio real continua fora do MVP local.

## Smoke HTTP

```text
health=true
initial_version=1
active_version=2
versions=2
footer_injected=true
body_has_cta=true
```
