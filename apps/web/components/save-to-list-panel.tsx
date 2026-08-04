'use client';

import { Check, Loader2, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { addCompaniesToList, createList, CompanySearchResult, fetchLists, ListSummary } from '../lib/api';

export function SaveToListPanel({
  companies,
  onClose,
  onSaved,
}: {
  companies: CompanySearchResult[];
  onClose: () => void;
  onSaved: (result: { listName: string; added: number }) => void;
}) {
  const [lists, setLists] = useState<ListSummary[] | null>(null);
  const [selectedListId, setSelectedListId] = useState<string>('');
  const [newListName, setNewListName] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLists()
      .then(setLists)
      .catch(() => setLists([]));
  }, []);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      let listId: number;
      let listName: string;

      if (newListName.trim()) {
        const created = await createList(newListName.trim());
        listId = created.id;
        listName = created.name;
      } else if (selectedListId) {
        listId = Number(selectedListId);
        listName = lists?.find((l) => l.id === listId)?.name || 'lista';
      } else {
        setError('Escolha uma lista existente ou digite o nome de uma nova.');
        setSaving(false);
        return;
      }

      const result = await addCompaniesToList(listId, companies);
      onSaved({ listName, added: result.added });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="absolute right-8 top-full z-10 mt-2 w-80 rounded-lg border border-zinc-200 bg-white p-4 shadow-lg">
      <p className="mb-3 text-sm font-semibold text-zinc-900">
        Salvar {companies.length} empresa{companies.length > 1 ? 's' : ''} em lista
      </p>

      <label className="mb-1 block text-xs font-medium text-zinc-500">Lista existente</label>
      <select
        value={selectedListId}
        onChange={(e) => {
          setSelectedListId(e.target.value);
          if (e.target.value) setNewListName('');
        }}
        disabled={!lists || lists.length === 0}
        className="mb-3 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 disabled:bg-zinc-50 disabled:text-zinc-400"
      >
        <option value="">{lists?.length ? 'Selecione…' : 'Nenhuma lista ainda'}</option>
        {lists?.map((list) => (
          <option key={list.id} value={list.id}>
            {list.name} ({list.companyCount})
          </option>
        ))}
      </select>

      <div className="mb-3 flex items-center gap-2 text-xs text-zinc-400">
        <div className="h-px flex-1 bg-zinc-200" />
        ou
        <div className="h-px flex-1 bg-zinc-200" />
      </div>

      <label className="mb-1 block text-xs font-medium text-zinc-500">Criar nova lista</label>
      <input
        value={newListName}
        onChange={(e) => {
          setNewListName(e.target.value);
          if (e.target.value) setSelectedListId('');
        }}
        placeholder="Nome da nova lista"
        className="mb-3 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
      />

      {error && <p className="mb-3 text-xs text-red-600">{error}</p>}

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="rounded-md px-3 py-1.5 text-sm text-zinc-500 hover:bg-zinc-50"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
          Salvar
        </button>
      </div>
    </div>
  );
}

export function SaveToListButton({ count, onClick }: { count: number; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
    >
      <Plus size={14} />
      Salvar {count} em lista
    </button>
  );
}
