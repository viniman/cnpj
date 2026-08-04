export interface CompanySearchQuery {
  q?: string;
  uf?: string;
  cnae?: string;
  situacao?: string;
  page?: string;
  pageSize?: string;
}

export interface NormalizedCompanySearchParams {
  q: string | null;
  uf: string | null;
  cnae: string | null;
  situacao: string | null;
  page: number;
  pageSize: number;
  offset: number;
}

export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;
export const MIN_QUERY_LENGTH = 2;

const UF_PATTERN = /^[A-Za-z]{2}$/;

function normalizeText(value: string | undefined): string | null {
  if (value === undefined || value === null) {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function normalizePositiveInt(value: string | undefined, fallback: number, max?: number): number {
  const parsed = Number.parseInt(value ?? '', 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return fallback;
  }
  return max ? Math.min(parsed, max) : parsed;
}

/**
 * Pure normalization/validation, kept separate from the raw SQL query
 * builder so it can be unit tested without a live database connection.
 */
export function normalizeCompanySearchParams(query: CompanySearchQuery): NormalizedCompanySearchParams {
  const rawQ = normalizeText(query.q);
  const q = rawQ && rawQ.length >= MIN_QUERY_LENGTH ? rawQ : null;

  const rawUf = normalizeText(query.uf);
  const uf = rawUf && UF_PATTERN.test(rawUf) ? rawUf.toUpperCase() : null;

  const cnae = normalizeText(query.cnae);
  const situacao = normalizeText(query.situacao);

  const page = normalizePositiveInt(query.page, 1);
  const pageSize = normalizePositiveInt(query.pageSize, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE);
  const offset = (page - 1) * pageSize;

  return { q, uf, cnae, situacao, page, pageSize, offset };
}
