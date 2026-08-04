'use client';

import { Loader2 } from 'lucide-react';
import { useState } from 'react';
import { createEmailAccount, EmailAccount, EmailAccountFormInput } from '../lib/api';

const inputClass =
  'w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500';
const labelClass = 'mb-1 block text-xs font-medium text-zinc-500';

export function EmailAccountForm({
  onCreated,
  onCancel,
}: {
  onCreated: (account: EmailAccount) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<EmailAccountFormInput>({
    name: '',
    fromName: '',
    fromEmail: '',
    smtpHost: 'email-smtp.us-east-1.amazonaws.com',
    smtpPort: 587,
    smtpSecure: false,
    smtpUser: '',
    smtpPassword: '',
    dailyLimit: 100,
    limitResetTimezone: 'UTC',
    delayMode: 'random',
    delayMinSeconds: 300,
    delayMaxSeconds: 420,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof EmailAccountFormInput>(key: K, value: EmailAccountFormInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createEmailAccount(form);
      onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-zinc-200 bg-white p-6">
      <p className="mb-4 text-sm font-semibold text-zinc-900">Nova conta de e-mail</p>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Nome da conta</label>
          <input
            required
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            placeholder="Ex.: Preparatório OLITEF"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Nome do remetente</label>
          <input
            required
            value={form.fromName}
            onChange={(e) => set('fromName', e.target.value)}
            className={inputClass}
          />
        </div>
        <div className="sm:col-span-2">
          <label className={labelClass}>E-mail do remetente</label>
          <input
            required
            type="email"
            value={form.fromEmail}
            onChange={(e) => set('fromEmail', e.target.value)}
            placeholder="contato@realgrana.com.br"
            className={inputClass}
          />
        </div>
      </div>

      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-400">SMTP (AWS SES)</p>
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <label className={labelClass}>Host</label>
          <input
            required
            value={form.smtpHost}
            onChange={(e) => set('smtpHost', e.target.value)}
            placeholder="email-smtp.us-east-1.amazonaws.com"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Porta</label>
          <input
            required
            type="number"
            value={form.smtpPort}
            onChange={(e) => set('smtpPort', Number(e.target.value))}
            className={inputClass}
          />
        </div>
        <div className="flex items-end pb-2">
          <label className="flex items-center gap-2 text-sm text-zinc-600">
            <input
              type="checkbox"
              checked={form.smtpSecure}
              onChange={(e) => set('smtpSecure', e.target.checked)}
              className="rounded border-zinc-300"
            />
            SSL (porta 465)
          </label>
        </div>
        <div>
          <label className={labelClass}>Usuário SMTP</label>
          <input
            required
            value={form.smtpUser}
            onChange={(e) => set('smtpUser', e.target.value)}
            className={inputClass}
          />
        </div>
        <div className="sm:col-span-3">
          <label className={labelClass}>Senha SMTP</label>
          <input
            required
            type="password"
            value={form.smtpPassword}
            onChange={(e) => set('smtpPassword', e.target.value)}
            placeholder="Credencial SMTP do SES, não a access key da AWS"
            className={inputClass}
          />
        </div>
      </div>

      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-400">Limite diário de envios</p>
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label className={labelClass}>Mensagens por dia</label>
          <input
            required
            type="number"
            min={1}
            value={form.dailyLimit}
            onChange={(e) => set('dailyLimit', Number(e.target.value))}
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Fuso horário de redefinição</label>
          <input
            value={form.limitResetTimezone}
            onChange={(e) => set('limitResetTimezone', e.target.value)}
            placeholder="UTC"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Modo de atraso</label>
          <select
            value={form.delayMode}
            onChange={(e) => set('delayMode', e.target.value as 'fixed' | 'random')}
            className={inputClass}
          >
            <option value="random">Aleatório (faixa)</option>
            <option value="fixed">Fixo</option>
          </select>
        </div>

        {form.delayMode === 'fixed' ? (
          <div>
            <label className={labelClass}>Atraso fixo (segundos)</label>
            <input
              type="number"
              min={1}
              value={form.delayFixedSeconds ?? ''}
              onChange={(e) => set('delayFixedSeconds', Number(e.target.value))}
              className={inputClass}
            />
          </div>
        ) : (
          <>
            <div>
              <label className={labelClass}>Atraso mínimo (segundos)</label>
              <input
                type="number"
                min={1}
                value={form.delayMinSeconds ?? ''}
                onChange={(e) => set('delayMinSeconds', Number(e.target.value))}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Atraso máximo (segundos)</label>
              <input
                type="number"
                min={1}
                value={form.delayMaxSeconds ?? ''}
                onChange={(e) => set('delayMaxSeconds', Number(e.target.value))}
                className={inputClass}
              />
            </div>
          </>
        )}
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md px-4 py-2 text-sm text-zinc-500 hover:bg-zinc-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {saving && <Loader2 size={16} className="animate-spin" />}
          Salvar conta
        </button>
      </div>
    </form>
  );
}
