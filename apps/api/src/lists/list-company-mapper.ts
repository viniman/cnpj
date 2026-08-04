export interface CompanyInput {
  cnpjBasico: string;
  cnpjOrdem: string;
  cnpjDv: string;
  razaoSocial: string;
  nomeFantasia?: string | null;
  situacaoCadastral?: string | null;
  uf?: string | null;
  municipioNome?: string | null;
  cnaeDescricao?: string | null;
  correioEletronico?: string | null;
}

export interface ListCompanyCreateData {
  listId: number;
  cnpjBasico: string;
  cnpjOrdem: string;
  cnpjDv: string;
  razaoSocial: string;
  nomeFantasia: string | null;
  situacaoCadastral: string | null;
  uf: string | null;
  municipioNome: string | null;
  cnaeDescricao: string | null;
  correioEletronico: string | null;
}

function normalize(value: string | null | undefined): string | null {
  if (value === undefined || value === null) return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/**
 * Pure mapping from a company search result into the ListCompany create
 * payload, kept separate from the Prisma call so the field
 * normalization can be unit tested without a database.
 */
export function toListCompanyData(listId: number, company: CompanyInput): ListCompanyCreateData {
  return {
    listId,
    cnpjBasico: company.cnpjBasico.trim(),
    cnpjOrdem: company.cnpjOrdem.trim(),
    cnpjDv: company.cnpjDv.trim(),
    razaoSocial: company.razaoSocial.trim(),
    nomeFantasia: normalize(company.nomeFantasia),
    situacaoCadastral: normalize(company.situacaoCadastral),
    uf: normalize(company.uf),
    municipioNome: normalize(company.municipioNome),
    cnaeDescricao: normalize(company.cnaeDescricao),
    correioEletronico: normalize(company.correioEletronico),
  };
}
