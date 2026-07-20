# Historico de Implementacao

Este arquivo registra as etapas realizadas no projeto para preservar contexto,
decisoes e criterios de verificacao.

## 2026-07-19 - Baseline do MVP local

Commit: `0d421d3 chore: establish local MVP baseline`

Estado registrado:

- Aplicacao local `Radar CNPJ Interno` em Python standard library + SQLite.
- Frontend estatico operacional em `static/`.
- Descoberta automatica da fonte oficial Receita/SERPRO via WebDAV.
- Consulta individual via BrasilAPI.
- Importacao de amostra CSV e parser limitado de ZIPs oficiais.
- Busca/filtros de empresas, detalhe com socios, listas, higiene de e-mail,
  supressao, exportacao CSV/XLSX e auditoria.
- Testes unitarios basicos passando.

Motivo do baseline:

- O diretorio ainda nao era um repositorio Git.
- A partir deste ponto, toda etapa relevante deve ter branch e commits
  atomicos seguindo Conventional Commits.

## Protocolo de trabalho

1. Criar branch `feature/<numero>-<slug>`.
2. Registrar docs ou decisao antes de implementar feature grande.
3. Fazer commits pequenos por unidade logica.
4. Rodar testes antes de encerrar a etapa.
5. Atualizar este historico com o que mudou e como verificar.

