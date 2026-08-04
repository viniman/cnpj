'use client';

import { ListChecks, Loader2, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ComingSoon } from '../../components/coming-soon';
import { PageHeader } from '../../components/page-header';
import { API_BASE_URL, fetchLists, ListSummary } from '../../lib/api';

export default function ListasPage() {
  const [lists, setLists] = useState<ListSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    fetchLists()
      .then(setLists)
      .catch(() => setError('Falha ao carregar listas.'));
  }

  useEffect(load, []);

  async function handleDelete(id: number) {
    if (!confirm('Excluir esta lista? Essa ação não pode ser desfeita.')) return;
    await fetch(`${API_BASE_URL}/lists/${id}`, { method: 'DELETE' });
    load();
  }

  return (
    <div>
      <PageHeader
        title="Listas"
        description="Salve empresas encontradas em Empresas para usar em campanhas."
      />
      <div className="px-8 py-6">
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        {lists === null && !error && (
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <Loader2 size={16} className="animate-spin" /> Carregando…
          </div>
        )}

        {lists && lists.length === 0 && (
          <ComingSoon
            icon={ListChecks}
            title="Nenhuma lista ainda"
            description='Vá em "Empresas", busque e selecione empresas, e clique em "Salvar em lista" para criar sua primeira lista.'
          />
        )}

        {lists && lists.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {lists.map((list) => (
              <div
                key={list.id}
                className="group relative rounded-lg border border-zinc-200 bg-white p-5 transition-colors hover:border-brand-300"
              >
                <Link href={`/listas/${list.id}`} className="block">
                  <p className="pr-6 text-sm font-semibold text-zinc-900">{list.name}</p>
                  {list.description && <p className="mt-1 text-xs text-zinc-500">{list.description}</p>}
                  <p className="mt-3 text-2xl font-semibold text-brand-600">{list.companyCount}</p>
                  <p className="text-xs text-zinc-400">empresa{list.companyCount === 1 ? '' : 's'}</p>
                </Link>
                <button
                  type="button"
                  onClick={() => handleDelete(list.id)}
                  className="absolute right-4 top-5 text-zinc-300 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
                  title="Excluir lista"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
