'use client';

import { CheckCircle2, Loader2, Mail, Plug, Plus, Trash2, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ComingSoon } from '../../../components/coming-soon';
import { EmailAccountForm } from '../../../components/email-account-form';
import { PageHeader } from '../../../components/page-header';
import { deleteEmailAccount, EmailAccount, fetchEmailAccounts, testEmailAccount } from '../../../lib/api';

function delaySummary(account: EmailAccount): string {
  if (account.delayMode === 'fixed') {
    return `Atraso fixo de ${account.delayFixedSeconds}s`;
  }
  return `Atraso de ${account.delayMinSeconds}–${account.delayMaxSeconds}s`;
}

export default function ConfigEmailPage() {
  const [accounts, setAccounts] = useState<EmailAccount[] | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<number, { ok: boolean; message: string }>>({});
  const [testingId, setTestingId] = useState<number | null>(null);

  function load() {
    fetchEmailAccounts()
      .then(setAccounts)
      .catch(() => setError('Falha ao carregar contas de e-mail.'));
  }

  useEffect(load, []);

  async function handleDelete(id: number) {
    if (!confirm('Excluir esta conta de e-mail?')) return;
    await deleteEmailAccount(id);
    load();
  }

  async function handleTest(id: number) {
    setTestingId(id);
    try {
      const result = await testEmailAccount(id);
      setTestResults((prev) => ({ ...prev, [id]: result }));
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [id]: { ok: false, message: err instanceof Error ? err.message : 'Erro ao testar.' },
      }));
    } finally {
      setTestingId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Configuração de e-mail"
        description="Conecte a conta SMTP (AWS SES) usada para disparar campanhas e defina o limite diário de envios."
        action={
          !showForm && (
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              <Plus size={14} /> Adicionar conta
            </button>
          )
        }
      />

      <div className="space-y-4 px-8 py-6">
        {error && <p className="text-sm text-red-600">{error}</p>}

        {showForm && (
          <EmailAccountForm
            onCancel={() => setShowForm(false)}
            onCreated={() => {
              setShowForm(false);
              load();
            }}
          />
        )}

        {accounts === null && !error && (
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <Loader2 size={16} className="animate-spin" /> Carregando…
          </div>
        )}

        {accounts && accounts.length === 0 && !showForm && (
          <ComingSoon
            icon={Mail}
            title="Nenhuma conta configurada"
            description='Clique em "Adicionar conta" para cadastrar as credenciais SMTP do AWS SES.'
          />
        )}

        {accounts && accounts.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {accounts.map((account) => {
              const result = testResults[account.id];
              return (
                <div key={account.id} className="rounded-lg border border-zinc-200 bg-white p-5">
                  <div className="mb-3 flex items-start justify-between">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900">{account.name}</p>
                      <p className="text-xs text-zinc-500">
                        {account.fromName} &lt;{account.fromEmail}&gt;
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDelete(account.id)}
                      className="text-zinc-300 hover:text-red-500"
                      title="Excluir conta"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <div className="mb-4 space-y-1 text-xs text-zinc-500">
                    <p>
                      {account.smtpHost}:{account.smtpPort} {account.smtpSecure ? '(SSL)' : ''}
                    </p>
                    <p>
                      {account.dailyLimit} e-mails/dia · redefine {account.limitResetTimezone} ·{' '}
                      {delaySummary(account)}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleTest(account.id)}
                      disabled={testingId === account.id}
                      className="flex items-center gap-1.5 rounded-md border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-60"
                    >
                      {testingId === account.id ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Plug size={13} />
                      )}
                      Testar conexão
                    </button>
                    {result && (
                      <span
                        className={`flex items-center gap-1 text-xs ${result.ok ? 'text-emerald-600' : 'text-red-600'}`}
                      >
                        {result.ok ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                        {result.message}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
