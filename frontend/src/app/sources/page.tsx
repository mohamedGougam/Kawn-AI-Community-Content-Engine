'use client';

import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { api, Source, SourceMapping, formatDate } from '@/lib/api';

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [mapping, setMapping] = useState<SourceMapping[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({ name: '', source_type: 'rss', url: '', category: '', is_active: true });

  const load = () => {
    api.getSources().then(setSources);
    api.getSourceMapping().then(setMapping);
  };
  useEffect(() => { load(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editId) await api.updateSource(editId, form);
    else await api.createSource(form);
    setShowForm(false);
    setEditId(null);
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sources</h1>
          <p className="text-[var(--muted)]">Manage RSS feeds, APIs, and trusted sources</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" /> Add Source
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            <select className="select" value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })}>
              <option value="rss">RSS Feed</option>
              <option value="news_api">News API</option>
              <option value="sports_api">Sports API</option>
              <option value="public_api">Public API</option>
              <option value="website">Website</option>
            </select>
            <input className="input md:col-span-2" placeholder="URL" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} required />
            <input className="input" placeholder="Category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">{editId ? 'Update' : 'Create'}</button>
            <button type="button" onClick={() => { setShowForm(false); setEditId(null); }} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--card-border)] text-left text-[var(--muted)]">
              <th className="px-6 py-3">Name</th>
              <th className="px-6 py-3">Type</th>
              <th className="px-6 py-3">Category</th>
              <th className="px-6 py-3">Reliability</th>
              <th className="px-6 py-3">Last Fetched</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="table-row">
                <td className="px-6 py-4 font-medium">{s.name}</td>
                <td className="px-6 py-4">{s.source_type}</td>
                <td className="px-6 py-4">{s.category || '—'}</td>
                <td className="px-6 py-4">{(Number(s.reliability_score) * 100).toFixed(0)}%</td>
                <td className="px-6 py-4">{formatDate(s.last_fetched_at)}</td>
                <td className="px-6 py-4">
                  <span className={`badge ${s.is_active ? 'badge-success' : 'badge-neutral'}`}>{s.is_active ? 'Active' : 'Inactive'}</span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button onClick={() => { setForm({ name: s.name, source_type: s.source_type, url: s.url, category: s.category || '', is_active: s.is_active }); setEditId(s.id); setShowForm(true); }} className="rounded p-1 hover:bg-white/10"><Pencil className="h-4 w-4" /></button>
                    <button onClick={async () => { if (confirm('Delete?')) { await api.deleteSource(s.id); load(); } }} className="rounded p-1 hover:bg-red-500/20"><Trash2 className="h-4 w-4 text-red-400" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 className="mb-2 text-lg font-semibold">Community → Source Mapping</h2>
        <p className="mb-4 text-sm text-[var(--muted)]">
          Each community fetches news from sources matching its category. When you generate a post, the engine collects from these sources first.
        </p>
        <div className="space-y-3">
          {mapping.map((m) => (
            <div key={m.community_id} className="rounded-lg border border-[var(--card-border)] p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{m.community_name}</span>
                <span className="badge badge-info">{m.category}</span>
              </div>
              {m.sources.length === 0 ? (
                <p className="mt-2 text-sm text-amber-400">No sources linked — posts will use fallback content.</p>
              ) : (
                <ul className="mt-2 space-y-1">
                  {m.sources.map((s) => (
                    <li key={s.id} className="flex flex-wrap items-center gap-2 text-sm text-[var(--muted)]">
                      <span className="text-white">{s.name}</span>
                      <span>({s.category})</span>
                      {s.last_fetched_at ? (
                        <span className="badge badge-success">Fetched {formatDate(s.last_fetched_at)}</span>
                      ) : (
                        <span className="badge badge-warning">Not fetched yet</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
