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

export interface ListSummary {
  id: number;
  name: string;
  description: string | null;
  createdAt: string;
  companyCount: number;
}

export interface ListCompany {
  id: number;
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
  addedAt: string;
}

export interface ListDetail {
  id: number;
  name: string;
  description: string | null;
  createdAt: string;
  companies: ListCompany[];
  companyCount: number;
  page: number;
  pageSize: number;
}

export async function fetchLists(): Promise<ListSummary[]> {
  const response = await fetch(`${API_BASE_URL}/lists`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Falha ao carregar listas.');
  return response.json();
}

export async function createList(name: string, description?: string): Promise<ListSummary> {
  const response = await fetch(`${API_BASE_URL}/lists`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.message || 'Falha ao criar lista.');
  }
  return response.json();
}

export async function addCompaniesToList(listId: number, companies: CompanySearchResult[]) {
  const response = await fetch(`${API_BASE_URL}/lists/${listId}/companies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ companies }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.message || 'Falha ao adicionar empresas à lista.');
  }
  return response.json() as Promise<{ added: number; requested: number }>;
}

export interface EmailAccount {
  id: number;
  name: string;
  fromName: string;
  fromEmail: string;
  smtpHost: string;
  smtpPort: number;
  smtpSecure: boolean;
  smtpUser: string;
  dailyLimit: number;
  limitResetTimezone: string;
  delayMode: 'fixed' | 'random';
  delayFixedSeconds: number | null;
  delayMinSeconds: number | null;
  delayMaxSeconds: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface EmailAccountFormInput {
  name: string;
  fromName: string;
  fromEmail: string;
  smtpHost: string;
  smtpPort: number;
  smtpSecure: boolean;
  smtpUser: string;
  smtpPassword?: string;
  dailyLimit: number;
  limitResetTimezone: string;
  delayMode: 'fixed' | 'random';
  delayFixedSeconds?: number;
  delayMinSeconds?: number;
  delayMaxSeconds?: number;
}

async function parseOrThrow<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.message || fallbackMessage);
  }
  return response.json();
}

export async function fetchEmailAccounts(): Promise<EmailAccount[]> {
  const response = await fetch(`${API_BASE_URL}/email-accounts`, { cache: 'no-store' });
  return parseOrThrow(response, 'Falha ao carregar contas de e-mail.');
}

export async function createEmailAccount(input: EmailAccountFormInput): Promise<EmailAccount> {
  const response = await fetch(`${API_BASE_URL}/email-accounts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  return parseOrThrow(response, 'Falha ao criar conta de e-mail.');
}

export async function deleteEmailAccount(id: number): Promise<void> {
  await fetch(`${API_BASE_URL}/email-accounts/${id}`, { method: 'DELETE' });
}

export async function testEmailAccount(id: number): Promise<{ ok: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/email-accounts/${id}/test`, { method: 'POST' });
  return parseOrThrow(response, 'Falha ao testar conexão.');
}
