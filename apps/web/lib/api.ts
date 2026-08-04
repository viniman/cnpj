export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:3001';

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

export interface CompanySearchResponse {
  results: CompanySearchResult[];
  page: number;
  pageSize: number;
}

export const SITUACAO_LABELS: Record<string, { label: string; className: string }> = {
  '01': { label: 'Nula', className: 'bg-zinc-100 text-zinc-600' },
  '02': { label: 'Ativa', className: 'bg-emerald-50 text-emerald-700' },
  '03': { label: 'Suspensa', className: 'bg-amber-50 text-amber-700' },
  '04': { label: 'Inapta', className: 'bg-red-50 text-red-700' },
  '08': { label: 'Baixada', className: 'bg-zinc-100 text-zinc-600' },
};

export function formatCnpj(cnpjBasico: string, cnpjOrdem: string, cnpjDv: string): string {
  return `${cnpjBasico}${cnpjOrdem}${cnpjDv}`.replace(
    /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
    '$1.$2.$3/$4-$5',
  );
}
