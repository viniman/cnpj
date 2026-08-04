'use client';

import { AlertCircle, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PageHeader } from '../../../components/page-header';
import {
  createCampaign,
  EmailAccount,
  fetchEmailAccounts,
  fetchLists,
  ListSummary,
} from '../../../lib/api';

const inputClass =
  'w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500';
const labelClass = 'mb-1 block text-xs font-medium text-zinc-500';

export default function NewCampaignPage() {
  const router = useRouter();
  const [lists, setLists] = useState<ListSummary[] | null>(null);
  const [accounts, setAccounts] = useState<EmailAccount[] | null>(null);
  const [name, setName] = useState('');
  const [listId, setListId] = useState('');
  const [emailAccountId, setEmailAccountId] = useState('');
  const [subject, setSubject] = useState('');
  const [bodyHtml, setBodyHtml] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLists().then(setLists).catch(() => setLists([]));
    fetchEmailAccounts().then(setAccounts).catch(() => setAccounts([]));
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!listId || !emailAccountId) {
      setError('Selecione uma lista e uma conta de e-mail.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const campaign = await createCampaign({
        name,
        listId: Number(listId),
        emailAccountId: Number(emailAccountId),
        subject,
        bodyHtml,
      });
      router.push(`/campanhas/${campaign.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar campanha.');
      setSaving(false);
    }
  }

  const listsReady = lists !== null;
  const accountsReady = accounts !== null;

  return (
    <div>
      <PageHeader title="Nova campanha" description="A campanha nasce em rascunho — nada é enviado até você iniciar." />

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-5 px-8 py-6">
        <div>
          <label className={labelClass}>Nome da campanha</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Lista</label>
            <select
              required
              value={listId}
              onChange={(e) => setListId(e.target.value)}
              disabled={!listsReady}
              className={inputClass}
            >
              <option value="">{listsReady ? 'Selecione…' : 'Carregando…'}</option>
              {lists?.map((list) => (
                <option key={list.id} value={list.id}>
                  {list.name} ({list.companyCount})
                </option>
              ))}
            </select>
            {listsReady && lists.length === 0 && (
              <p className="mt-1 text-xs text-amber-600">Nenhuma lista salva ainda — crie uma em Empresas.</p>
            )}
          </div>
          <div>
            <label className={labelClass}>Conta de e-mail</label>
            <select
              required
              value={emailAccountId}
              onChange={(e) => setEmailAccountId(e.target.value)}
              disabled={!accountsReady}
              className={inputClass}
            >
              <option value="">{accountsReady ? 'Selecione…' : 'Carregando…'}</option>
              {accounts?.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
            {accountsReady && accounts.length === 0 && (
              <p className="mt-1 text-xs text-amber-600">
                Nenhuma conta configurada ainda — crie uma em Config. de e-mail.
              </p>
            )}
          </div>
        </div>

        <div>
          <label className={labelClass}>Assunto</label>
          <input
            required
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Ex.: {{razaoSocial}}, uma proposta para você"
            className={inputClass}
          />
        </div>

        <div>
          <label className={labelClass}>Corpo do e-mail (HTML)</label>
          <textarea
            required
            rows={10}
            value={bodyHtml}
            onChange={(e) => setBodyHtml(e.target.value)}
            placeholder={'<p>Olá {{razaoSocial}},</p>\n<p>...</p>'}
            className={`${inputClass} font-mono text-xs`}
          />
          <p className="mt-1 text-xs text-zinc-400">
            Variáveis disponíveis: <code>{'{{razaoSocial}}'}</code>, <code>{'{{nomeFantasia}}'}</code>,{' '}
            <code>{'{{municipioNome}}'}</code>. O link de descadastro é adicionado automaticamente no rodapé.
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {saving && <Loader2 size={16} className="animate-spin" />}
            Criar campanha (rascunho)
          </button>
        </div>
      </form>
    </div>
  );
}
