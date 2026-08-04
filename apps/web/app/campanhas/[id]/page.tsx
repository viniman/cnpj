'use client';

import { AlertTriangle, Loader2, Pause, Play, Trash2 } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PageHeader } from '../../../components/page-header';
import {
  CAMPAIGN_STATUS_LABELS,
  CampaignDetail,
  deleteCampaign,
  fetchCampaign,
  pauseCampaign,
  startCampaign,
} from '../../../lib/api';

const RECIPIENT_STATUS_LABELS: Record<string, { label: string; className: string }> = {
  pending: { label: 'Pendente', className: 'bg-zinc-100 text-zinc-600' },
  sent: { label: 'Enviado', className: 'bg-emerald-50 text-emerald-700' },
  failed: { label: 'Falhou', className: 'bg-red-50 text-red-700' },
  skipped_no_email: { label: 'Sem e-mail', className: 'bg-zinc-100 text-zinc-500' },
  skipped_suppressed: { label: 'Descadastrado', className: 'bg-amber-50 text-amber-700' },
};

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const campaignId = params.id;

  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmingStart, setConfirmingStart] = useState(false);

  function load() {
    fetchCampaign(Number(campaignId))
      .then(setCampaign)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [campaignId]);

  // Poll while active so counts/status update live without a manual refresh.
  useEffect(() => {
    if (campaign?.status !== 'active') return;
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [campaign?.status, campaignId]);

  async function handleStart() {
    setBusy(true);
    try {
      await startCampaign(Number(campaignId));
      setConfirmingStart(false);
      load();
    } finally {
      setBusy(false);
    }
  }

  async function handlePause() {
    setBusy(true);
    try {
      await pauseCampaign(Number(campaignId));
      load();
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!confirm('Excluir esta campanha? Essa ação não pode ser desfeita.')) return;
    await deleteCampaign(Number(campaignId));
    router.push('/campanhas');
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Campanha" />
        <div className="px-8 py-6 text-sm text-red-600">{error}</div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div>
        <PageHeader title="Campanha" />
        <div className="flex items-center gap-2 px-8 py-6 text-sm text-zinc-500">
          <Loader2 size={16} className="animate-spin" /> Carregando…
        </div>
      </div>
    );
  }

  const status = CAMPAIGN_STATUS_LABELS[campaign.status];
  const canStart = campaign.status === 'draft' || campaign.status === 'paused';
  const canPause = campaign.status === 'active';

  return (
    <div>
      <PageHeader
        title={campaign.name}
        description={`Lista: ${campaign.list.name} · Conta: ${campaign.emailAccount.name}`}
        action={
          <div className="flex items-center gap-2">
            <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${status.className}`}>{status.label}</span>
            {canPause && (
              <button
                type="button"
                onClick={handlePause}
                disabled={busy}
                className="flex items-center gap-1.5 rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-60"
              >
                <Pause size={14} /> Pausar
              </button>
            )}
            {canStart && !confirmingStart && (
              <button
                type="button"
                onClick={() => setConfirmingStart(true)}
                className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
              >
                <Play size={14} /> Iniciar campanha
              </button>
            )}
            <button
              type="button"
              onClick={handleDelete}
              className="text-zinc-300 hover:text-red-500"
              title="Excluir campanha"
            >
              <Trash2 size={16} />
            </button>
          </div>
        }
      />

      {confirmingStart && (
        <div className="mx-8 mt-6 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="font-medium">
              Isso vai enviar e-mails de verdade para {campaign.counts.pending} destinatário(s), respeitando o
              limite diário e o atraso da conta "{campaign.emailAccount.name}".
            </p>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={handleStart}
                disabled={busy}
                className="rounded-md bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-700 disabled:opacity-60"
              >
                {busy ? 'Iniciando…' : 'Confirmar início'}
              </button>
              <button
                type="button"
                onClick={() => setConfirmingStart(false)}
                className="rounded-md px-3 py-1.5 text-xs text-amber-800 hover:bg-amber-100"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 px-8 py-6 sm:grid-cols-5">
        {(['total', 'sent', 'pending', 'failed', 'skipped_suppressed'] as const).map((key) => (
          <div key={key} className="rounded-lg border border-zinc-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-400">
              {key === 'total'
                ? 'Total'
                : key === 'sent'
                  ? 'Enviados'
                  : key === 'pending'
                    ? 'Pendentes'
                    : key === 'failed'
                      ? 'Falhas'
                      : 'Descadastrados'}
            </p>
            <p className="mt-1 text-2xl font-semibold text-zinc-900">{campaign.counts[key]}</p>
          </div>
        ))}
      </div>

      <div className="px-8 pb-10">
        <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-medium">Empresa</th>
                <th className="px-4 py-3 font-medium">E-mail</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Enviado em</th>
                <th className="px-4 py-3 font-medium">Erro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {campaign.recipients.map((recipient) => {
                const recipientStatus = RECIPIENT_STATUS_LABELS[recipient.status] || {
                  label: recipient.status,
                  className: 'bg-zinc-100 text-zinc-600',
                };
                return (
                  <tr key={recipient.id} className="hover:bg-zinc-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-zinc-900">{recipient.razaoSocial}</p>
                      {recipient.nomeFantasia && <p className="text-xs text-zinc-500">{recipient.nomeFantasia}</p>}
                    </td>
                    <td className="px-4 py-3 text-zinc-600">{recipient.email || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${recipientStatus.className}`}>
                        {recipientStatus.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-zinc-600">
                      {recipient.sentAt ? new Date(recipient.sentAt).toLocaleString('pt-BR') : '—'}
                    </td>
                    <td className="max-w-[240px] truncate px-4 py-3 text-xs text-red-600" title={recipient.errorMessage || ''}>
                      {recipient.errorMessage || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
