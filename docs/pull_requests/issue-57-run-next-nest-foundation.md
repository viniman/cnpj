# PR - Issue 57: Instalar dependências e rodar fundação Next/Nest

## Contexto

A fundação Next.js/NestJS existia sem `node_modules`. Com espaço suficiente no
drive `D:`, esta PR instala dependências, gera lockfile, valida builds e deixa
os servidores locais rodando para visualização.

Issue: #57

## Implementado

- Gerado `package-lock.json`.
- Instaladas dependências do workspace com cache em `data/npm-cache/`.
- Atualizado `.gitignore` para ignorar `.next/` e `data/npm-cache/`.
- Atualizado NestJS para 11.x.
- Ajustado `apps/web/next.config.mjs` com `outputFileTracingRoot`.
- Mantido `apps/web/next-env.d.ts` no formato gerado pelo Next 15.
- Atualizada documentação de execução em `docs/NEXT_NEST_FOUNDATION.md`.

## Como verificar

```powershell
npm.cmd --workspace apps/api run build
npm.cmd --workspace apps/web run build
python -m unittest tests.test_next_nest_foundation
```

Rodar localmente:

```powershell
npm.cmd --workspace apps/api run start:dev
npm.cmd --workspace apps/web run dev
```

URLs:

```text
http://127.0.0.1:3001/health
http://127.0.0.1:3001/receita/status
http://127.0.0.1:3000/
```

## Resultado validado

```text
Nest build: OK
Next build: OK
tests.test_next_nest_foundation: OK
GET /health: {"ok":true,"service":"radar-cnpj-api"}
GET /receita/status: schema receita_staging
GET /: HTTP 200
```

## Checklist

- [x] `npm install` concluído com cache local.
- [x] `package-lock.json` versionado.
- [x] NestJS compila.
- [x] Next.js compila.
- [x] API health responde.
- [x] Web abre localmente.
- [x] PR inclui checklist e comandos de teste.

## Observações

- `npm audit --omit=dev` ainda aponta vulnerabilidades transitivas do Next em
  `postcss`/`sharp`.
- Não foi aplicado `npm audit fix --force` porque a sugestão atual envolve
  downgrade/breaking change inadequado.
