'use client';

import { AlertCircle, Loader2, Search } from 'lucide-react';
import { useState } from 'react';
import { PageHeader } from '../../components/page-header';
import {
  API_BASE_URL,
  CompanySearchResult,
  formatCnpj,
  SITUACAO_LABELS,
} from '../../lib/api';

interface Filters {
  q: string;
  uf: string;
  cnae: string;
  situacao: string;
}

const EMPTY_FILTERS: Filters = { q: '', uf: '', cnae: '', situacao: '' };

export default function EmpresasPage() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [results, setResults] = useState<CompanySearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(event?: React.FormEvent) {
    event?.preventDefault();

    const params = new URLSearchParams();
    if (filters.q.trim()) params.set('q', filters.q.trim());
    if (filters.uf.trim()) params.set('uf', filters.uf.trim());
    if (filters.cnae.trim()) params.set('cnae', filters.cnae.trim());
    if (filters.situacao.trim()) params.set('situacao', filters.situacao.trim());

    if (!params.toString()) {
      setError('Informe ao menos um filtro: nome/CNPJ, UF, CNAE ou situação.');
      setResults(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/companies/search?${params.toString()}`);
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.message || `Busca falhou (HTTP ${response.status}).`);
      }
      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro inesperado na busca.');
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Base oficial"
        title="Empresas"
        description="Busque no cadastro nacional de CNPJ por nome, UF, CNAE ou situação cadastral."
      />

      <form onSubmit={runSearch} className="flex flex-wrap items-end gap-3 px-8 py-6">
        <div className="min-w-[240px] flex-1">
          <label className="mb-1 block text-xs font-medium text-zinc-500">Razão social, nome fantasia ou CNPJ</label>
          <input
            value={filters.q}
            onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
            placeholder="Ex.: Petrobras"
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <div className="w-24">
          <label className="mb-1 block text-xs font-medium text-zinc-500">UF</label>
          <input
            value={filters.uf}
            onChange={(e) => setFilters((f) => ({ ...f, uf: e.target.value }))}
            placeholder="SP"
            maxLength={2}
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm uppercase outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <div className="w-36">
          <label className="mb-1 block text-xs font-medium text-zinc-500">CNAE</label>
          <input
            value={filters.cnae}
            onChange={(e) => setFilters((f) => ({ ...f, cnae: e.target.value }))}
            placeholder="4711302"
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <div className="w-40">
          <label className="mb-1 block text-xs font-medium text-zinc-500">Situação</label>
          <select
            value={filters.situacao}
            onChange={(e) => setFilters((f) => ({ ...f, situacao: e.target.value }))}
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          >
            <option value="">Todas</option>
            <option value="02">Ativa</option>
            <option value="03">Suspensa</option>
            <option value="04">Inapta</option>
            <option value="08">Baixada</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          Buscar
        </button>
      </form>

      <div className="px-8 pb-10">
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {!results && !error && (
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-200 bg-white px-8 py-20 text-center text-sm text-zinc-500">
            Use os filtros acima para consultar o cadastro oficial de CNPJ.
          </div>
        )}

        {results && results.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-200 bg-white px-8 py-20 text-center text-sm text-zinc-500">
            Nenhuma empresa encontrada para esses filtros.
          </div>
        )}

        {results && results.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Empresa</th>
                  <th className="px-4 py-3 font-medium">CNPJ</th>
                  <th className="px-4 py-3 font-medium">Situação</th>
                  <th className="px-4 py-3 font-medium">Localização</th>
                  <th className="px-4 py-3 font-medium">CNAE</th>
                  <th className="px-4 py-3 font-medium">E-mail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {results.map((company) => {
                  const situacao = company.situacaoCadastral ? SITUACAO_LABELS[company.situacaoCadastral] : null;
                  return (
                    <tr key={`${company.cnpjBasico}${company.cnpjOrdem}${company.cnpjDv}`} className="hover:bg-zinc-50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-zinc-900">{company.razaoSocial?.trim()}</p>
                        {company.nomeFantasia && (
                          <p className="text-xs text-zinc-500">{company.nomeFantasia}</p>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-zinc-600">
                        {formatCnpj(company.cnpjBasico, company.cnpjOrdem, company.cnpjDv)}
                      </td>
                      <td className="px-4 py-3">
                        {situacao ? (
                          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${situacao.className}`}>
                            {situacao.label}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="px-4 py-3 text-zinc-600">
                        {company.municipioNome ? `${company.municipioNome}, ${company.uf}` : company.uf || '—'}
                      </td>
                      <td className="max-w-[220px] truncate px-4 py-3 text-zinc-600" title={company.cnaeDescricao || ''}>
                        {company.cnaeDescricao || company.cnaeFiscalPrincipal || '—'}
                      </td>
                      <td className="px-4 py-3 text-zinc-600">{company.correioEletronico || '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
