import { BadRequestException, Injectable } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma.service';
import { CompanySearchQuery, normalizeCompanySearchParams } from './company-search-params';

export interface CompanySearchResult {
  cnpjBasico: string;
  cnpjOrdem: string;
  cnpjDv: string;
  razaoSocial: string;
  nomeFantasia: string | null;
  situacaoCadastral: string | null;
  uf: string | null;
  municipio: string | null;
  municipioNome: string | null;
  cnaeFiscalPrincipal: string | null;
  cnaeDescricao: string | null;
  correioEletronico: string | null;
  identificadorMatrizFilial: string | null;
}

@Injectable()
export class CompaniesService {
  constructor(private readonly prisma: PrismaService) {}

  async search(query: CompanySearchQuery): Promise<{
    results: CompanySearchResult[];
    page: number;
    pageSize: number;
  }> {
    const params = normalizeCompanySearchParams(query);

    if (!params.q && !params.uf && !params.cnae && !params.situacao) {
      throw new BadRequestException('Informe ao menos um filtro: q, uf, cnae ou situacao.');
    }

    // The text search is resolved to a small cnpj_basico set FIRST (CTE),
    // each branch using its own trigram/btree index, then joined OUT to
    // the big tables. Filtering razao_social/nome_fantasia together in a
    // single post-join WHERE (across two tables) prevents Postgres from
    // using either trigram index and forces a sequential scan of both
    // 70M-row tables — verified with EXPLAIN while building this query.
    const matchedCte = params.q
      ? Prisma.sql`
          matched AS (
            SELECT cnpj_basico FROM receita_staging.empresas_raw WHERE razao_social ILIKE ${`%${params.q}%`}
            UNION
            SELECT cnpj_basico FROM receita_staging.estabelecimentos_raw WHERE nome_fantasia ILIKE ${`%${params.q}%`}
            UNION
            SELECT cnpj_basico FROM receita_staging.empresas_raw WHERE cnpj_basico = ${params.q}
          )
        `
      : null;

    const conditions: Prisma.Sql[] = [];
    if (matchedCte) {
      conditions.push(Prisma.sql`e.cnpj_basico IN (SELECT cnpj_basico FROM matched)`);
    }
    if (params.uf) {
      conditions.push(Prisma.sql`e.uf = ${params.uf}`);
    }
    if (params.cnae) {
      conditions.push(Prisma.sql`e.cnae_fiscal_principal = ${params.cnae}`);
    }
    if (params.situacao) {
      conditions.push(Prisma.sql`e.situacao_cadastral = ${params.situacao}`);
    }

    const whereClause = conditions.length > 0 ? Prisma.sql`WHERE ${Prisma.join(conditions, ' AND ')}` : Prisma.empty;
    const withClause = matchedCte ? Prisma.sql`WITH ${matchedCte}` : Prisma.empty;

    // Snapshot unico (2026-07) hoje; quando houver historico mensal (issue
    // futura ligada a docs/NEXT_ARCHITECTURE_LEDGER.md), filtrar pelo
    // snapshot mais recente por cnpj_basico.
    const rows = await this.prisma.$queryRaw<CompanySearchResult[]>(Prisma.sql`
      ${withClause}
      SELECT
        e.cnpj_basico AS "cnpjBasico",
        e.cnpj_ordem AS "cnpjOrdem",
        e.cnpj_dv AS "cnpjDv",
        emp.razao_social AS "razaoSocial",
        e.nome_fantasia AS "nomeFantasia",
        e.situacao_cadastral AS "situacaoCadastral",
        e.uf AS "uf",
        e.municipio AS "municipio",
        mun.descricao AS "municipioNome",
        e.cnae_fiscal_principal AS "cnaeFiscalPrincipal",
        cnae.descricao AS "cnaeDescricao",
        e.correio_eletronico AS "correioEletronico",
        e.identificador_matriz_filial AS "identificadorMatrizFilial"
      FROM receita_staging.estabelecimentos_raw e
      JOIN receita_staging.empresas_raw emp ON emp.cnpj_basico = e.cnpj_basico
      LEFT JOIN receita_staging.municipios_raw mun ON mun.codigo = e.municipio
      LEFT JOIN receita_staging.cnaes_raw cnae ON cnae.codigo = e.cnae_fiscal_principal
      ${whereClause}
      ORDER BY emp.razao_social
      LIMIT ${params.pageSize} OFFSET ${params.offset}
    `);

    return { results: rows, page: params.page, pageSize: params.pageSize };
  }
}
