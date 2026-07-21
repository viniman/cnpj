# Fase 26 - Auditoria por workspace ativo

## Objetivo

Migrar a leitura de auditoria operacional para o workspace ativo. O operador
deve trocar a empresa na topbar e ver apenas os eventos de auditoria daquele
contexto, mantendo logs globais/sensiveis fora do escopo desta tela local.

## Escopo

- Migrar `audit_events` para `current_org_id(conn)`.
- Garantir que `/api/audit` respeita o mesmo contexto operacional das demais
  superficies migradas.
- Cobrir isolamento entre workspace interno e workspace secundario com teste.
- Preservar a funcao `audit` como ponto unico de gravacao de logs.

## Fora do escopo desta fase

- Auditoria global cross-workspace para administrador.
- Filtros por usuario, acao, periodo ou entidade.
- Politica append-only forte em banco.
- RBAC para diferenciar operador e administrador.

## Decisao central

A auditoria exibida no MVP local deve seguir o workspace ativo por padrao. Uma
visao global futura precisa ser explicita, protegida por permissao e diferente
da tela operacional usada no dia a dia.

## Criterios de aceite

- `/api/audit` e `audit_events` leem `current_org_id(conn)`.
- Trocar para workspace secundario oculta eventos do workspace interno.
- Evento criado no workspace secundario aparece apenas quando ele esta ativo.
- Voltar ao workspace interno restaura seus eventos de auditoria.
- Teste automatizado prova isolamento de leitura.
