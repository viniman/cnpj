import { Activity, Building2, ListChecks, Send } from 'lucide-react';
import Link from 'next/link';
import { PageHeader } from '../components/page-header';

const API_URL = process.env.API_URL || 'http://127.0.0.1:3001';

async function getApiStatus() {
  try {
    const response = await fetch(`${API_URL}/receita/status`, { cache: 'no-store' });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const status = await getApiStatus();

  const shortcuts = [
    { href: '/empresas', label: 'Buscar empresas', icon: Building2 },
    { href: '/listas', label: 'Ver listas', icon: ListChecks },
    { href: '/campanhas', label: 'Ver campanhas', icon: Send },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Visão geral"
        title="Radar CNPJ"
        description="Inteligência comercial B2B a partir dos dados públicos oficiais de CNPJ."
      />
      <div className="grid grid-cols-1 gap-4 px-8 py-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border border-zinc-200 bg-white p-5">
          <div className="mb-3 flex items-center gap-2 text-zinc-400">
            <Activity size={16} />
            <span className="text-xs font-medium uppercase tracking-wide">Status da API</span>
          </div>
          <p className="text-2xl font-semibold text-zinc-900">{status ? 'Conectada' : 'Aguardando'}</p>
          <p className="mt-1 text-sm text-zinc-500">Fonte: {status?.schema || 'receita_staging'}</p>
        </div>

        {shortcuts.map((shortcut) => {
          const Icon = shortcut.icon;
          return (
            <Link
              key={shortcut.href}
              href={shortcut.href}
              className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-5 transition-colors hover:border-brand-300 hover:bg-brand-50/40"
            >
              <div>
                <p className="text-sm font-medium text-zinc-900">{shortcut.label}</p>
                <p className="mt-1 text-xs text-zinc-500">Ir para a seção</p>
              </div>
              <Icon size={20} className="text-brand-600" strokeWidth={2} />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
