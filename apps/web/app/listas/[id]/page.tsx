'use client';

import { ArrowLeft, Loader2, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PageHeader } from '../../../components/page-header';
import { API_BASE_URL, formatCnpj, ListDetail, SITUACAO_LABELS } from '../../../lib/api';

export default function ListDetailPage() {
  const params = useParams<{ id: string }>();
  const listId = params.id;

  const [list, setList] = useState<ListDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    fetch(`${API_BASE_URL}/lists/${listId}`, { cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error('Lista não encontrada.');
        return res.json();
      })
      .then(setList)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [listId]);

  async function handleRemove(companyId: number) {
    await fetch(`${API_BASE_URL}/lists/${listId}/companies/${companyId}`, { method: 'DELETE' });
    load();
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Lista" />
        <div className="px-8 py-6 text-sm text-red-600">{error}</div>
      </div>
    );
  }

  if (!list) {
    return (
      <div>
        <PageHeader title="Lista" />
        <div className="flex items-center gap-2 px-8 py-6 text-sm text-zinc-500">
          <Loader2 size={16} className="animate-spin" /> Carregando…
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow={
          <Link href="/listas" className="flex items-center gap-1 text-brand-600 hover:underline">
            <ArrowLeft size={14} /> Listas
          </Link>
        }
        title={list.name}
        description={list.description || `${list.companyCount} empresa(s) salva(s).`}
      />

      <div className="px-8 pb-10">
        {list.companies.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-200 bg-white px-8 py-20 text-center text-sm text-zinc-500">
            Nenhuma empresa nesta lista ainda. Adicione pela página Empresas.
          </div>
        ) : (
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
                  <th className="w-10 px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {list.companies.map((company) => {
                  const situacao = company.situacaoCadastral ? SITUACAO_LABELS[company.situacaoCadastral] : null;
                  return (
                    <tr key={company.id} className="group hover:bg-zinc-50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-zinc-900">{company.razaoSocial}</p>
                        {company.nomeFantasia && <p className="text-xs text-zinc-500">{company.nomeFantasia}</p>}
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
                        {company.cnaeDescricao || '—'}
                      </td>
                      <td className="px-4 py-3 text-zinc-600">{company.correioEletronico || '—'}</td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => handleRemove(company.id)}
                          className="text-zinc-300 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
                          title="Remover da lista"
                        >
                          <Trash2 size={15} />
                        </button>
                      </td>
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
