'use client';

import { Loader2, Plus, Send } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ComingSoon } from '../../components/coming-soon';
import { PageHeader } from '../../components/page-header';
import { CAMPAIGN_STATUS_LABELS, CampaignSummary, fetchCampaigns } from '../../lib/api';

export default function CampanhasPage() {
  const [campaigns, setCampaigns] = useState<CampaignSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCampaigns()
      .then(setCampaigns)
      .catch(() => setError('Falha ao carregar campanhas.'));
  }, []);

  return (
    <div>
      <PageHeader
        title="Campanhas"
        description="Dispare e acompanhe campanhas de e-mail para as listas salvas."
        action={
          <Link
            href="/campanhas/novo"
            className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
          >
            <Plus size={14} /> Nova campanha
          </Link>
        }
      />

      <div className="px-8 py-6">
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        {campaigns === null && !error && (
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <Loader2 size={16} className="animate-spin" /> Carregando…
          </div>
        )}

        {campaigns && campaigns.length === 0 && (
          <ComingSoon
            icon={Send}
            title="Nenhuma campanha ainda"
            description='Clique em "Nova campanha" para escolher uma lista, uma conta de e-mail e escrever o conteúdo.'
          />
        )}

        {campaigns && campaigns.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Campanha</th>
                  <th className="px-4 py-3 font-medium">Lista</th>
                  <th className="px-4 py-3 font-medium">Conta</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Enviados</th>
                  <th className="px-4 py-3 font-medium">Pendentes</th>
                  <th className="px-4 py-3 font-medium">Falhas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {campaigns.map((campaign) => {
                  const status = CAMPAIGN_STATUS_LABELS[campaign.status];
                  return (
                    <tr key={campaign.id} className="hover:bg-zinc-50">
                      <td className="px-4 py-3">
                        <Link href={`/campanhas/${campaign.id}`} className="font-medium text-brand-700 hover:underline">
                          {campaign.name}
                        </Link>
                        <p className="text-xs text-zinc-500">{campaign.subject}</p>
                      </td>
                      <td className="px-4 py-3 text-zinc-600">{campaign.list.name}</td>
                      <td className="px-4 py-3 text-zinc-600">{campaign.emailAccount.name}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${status.className}`}>
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-600">
                        {campaign.counts.sent}/{campaign.counts.total}
                      </td>
                      <td className="px-4 py-3 text-zinc-600">{campaign.counts.pending}</td>
                      <td className="px-4 py-3 text-zinc-600">{campaign.counts.failed}</td>
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
