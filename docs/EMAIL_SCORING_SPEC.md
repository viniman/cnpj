# Especificacao do Scoring Avancado de E-mail

Esta especificacao guia a primeira fatia funcional nova apos o MVP.

## Objetivo

Classificar e pontuar e-mails para prospeccao B2B, explicando o motivo do
score e reduzindo prioridade de contatos ruins, genericos, pessoais,
descartaveis ou terceirizados.

## Entradas

- E-mail.
- Empresa vinculada.
- Socios/administradores da empresa.
- Quantidade de CNPJs distintos usando o mesmo e-mail.
- Quantidade de CNPJs distintos usando o mesmo dominio.
- Lista de supressao e opt-out.
- Resultado de higiene existente.
- Dominio oficial/enriquecido da empresa, quando houver.

## Classificacoes

- `invalid`: formato invalido.
- `suppressed`: presente em supressao ou opt-out.
- `disposable`: dominio descartavel.
- `personal_domain`: dominio pessoal conhecido.
- `generic_inbox`: caixa generica.
- `role_inbox`: caixa de area/função.
- `decision_maker`: prefixo associado a decisor.
- `nominal`: aparencia de nome proprio.
- `partner_match`: local-part bate com socio/administrador.
- `company_domain_match`: dominio bate com dominio da empresa.
- `shared_contact`: mesmo e-mail aparece em muitos CNPJs.
- `shared_domain`: dominio aparece em muitos CNPJs sem ser provedor comum.

## Dicionario base de prefixos

| Prefixo | Area | Peso |
|---|---|---:|
| contato, atendimento, sac, suporte, info | atendimento generico | 25 |
| contabil, contabilidade, fiscal, escritorio | contabil/fiscal | 10 |
| financeiro, cobranca, contas | financeiro | 35 |
| rh, recursoshumanos, vagas | recursos humanos | 35 |
| comercial, vendas, sales | comercial | 55 |
| juridico, compliance | juridico | 25 |
| diretoria, presidencia, ceo, socio, dono | decisor | 80 |
| ti, dev, sistemas | tecnologia | 45 |

## Regras de score

Score inicial: `50`.

Aplicacoes:

- Formato invalido: score `0`.
- Supressao/opt-out: score maximo `0`.
- Dominio descartavel: `-60`.
- Dominio pessoal: `-25`.
- Prefixo conhecido: substitui ou ajusta score base pelo peso da area.
- E-mail nominal: `+15`.
- Local-part bate com socio/administrador: `+30`.
- Dominio bate com site/domino oficial: `+20`.
- Mesmo e-mail em 3+ CNPJs: `-55` e flag `shared_contact`.
- Mesmo dominio em 5+ CNPJs: `-35` e flag `shared_domain`.
- Dominio conhecido como terceirizado: score maximo `25`.
- Higiene `Invalido`: score `0`.
- Higiene `Suspeito`: `-30`.

Score final fica entre `0` e `100`.

## Exemplos

1. `marina@novapilha.com.br`
   - nominal + dominio corporativo + possivel match com socio.
   - score esperado: alto.

2. `contato@empresa.com.br`
   - generico, mas corporativo.
   - score esperado: medio-baixo.

3. `contabil@assessoriacontabil.com.br`
   - area contabil e possivel dominio compartilhado.
   - score esperado: baixo.

4. `ceo@empresa.com.br`
   - decisor + corporativo.
   - score esperado: alto.

5. `teste@mailinator.com`
   - descartavel/suspeito.
   - score esperado: muito baixo.

## Persistencia planejada

- `email_classifications`: classificacao corrente por empresa/e-mail.
- `known_shared_domains`: dominios marcados como prestadores compartilhados.
- `email_score_log`: historico de recomputo com algoritmo e motivos.

## Criterios de aceite da fase

- Testes provam que e-mail nominal de socio tem score maior que generico.
- Testes provam que e-mail compartilhado por 3+ CNPJs e rebaixado.
- Testes provam que dominio descartavel ou opt-out recebe score restritivo.
- API retorna score e motivos.
- UI mostra o score e a explicacao.

