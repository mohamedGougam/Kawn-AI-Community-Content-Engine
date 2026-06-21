'use client';

import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Sparkles } from 'lucide-react';
import { api, Community } from '@/lib/api';

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [form, setForm] = useState({
    name: '', description: '', category: '', tags: '', blocked_topics: '',
    country: '', preferred_tone: 'friendly', is_child_safe: false, is_active: true,
  });

  const load = () => api.getCommunities().then(setCommunities).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const resetForm = () => {
    setForm({ name: '', description: '', category: '', tags: '', blocked_topics: '', country: '', preferred_tone: 'friendly', is_child_safe: false, is_active: true });
    setEditId(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name: form.name,
      description: form.description || null,
      category: form.category,
      tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
      blocked_topics: form.blocked_topics.split(',').map((t) => t.trim()).filter(Boolean),
      country: form.country || null,
      preferred_tone: form.preferred_tone,
      is_child_safe: form.is_child_safe,
      is_active: form.is_active,
    };
    if (editId) {
      await api.updateCommunity(editId, payload);
    } else {
      await api.createCommunity(payload);
    }
    resetForm();
    load();
  };

  const handleEdit = (c: Community) => {
    setForm({
      name: c.name, description: c.description || '', category: c.category,
      tags: c.tags.join(', '), blocked_topics: c.blocked_topics.join(', '),
      country: c.country || '', preferred_tone: c.preferred_tone,
      is_child_safe: c.is_child_safe, is_active: c.is_active,
    });
    setEditId(c.id);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this community?')) return;
    await api.deleteCommunity(id);
    load();
  };

  const handleGenerate = async (id: string, name: string) => {
    setGeneratingId(id);
    setMessage(null);
    try {
      const post = await api.generatePost(id);
      setMessage({
        type: 'success',
        text: `Post generated for ${name}: "${post.title}" — view it in Generated Posts.`,
      });
    } catch (e) {
      setMessage({
        type: 'error',
        text: `Failed to generate post for ${name}. ${e instanceof Error ? e.message : 'Please try again.'}`,
      });
    } finally {
      setGeneratingId(null);
    }
  };

  if (loading) return <div className="text-[var(--muted)]">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Communities</h1>
          <p className="text-[var(--muted)]">Manage community settings and personalization</p>
        </div>
        <button onClick={() => { resetForm(); setShowForm(true); }} className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" /> Add Community
        </button>
      </div>

      {message && (
        <div className={`card ${message.type === 'success' ? 'border-emerald-500/40' : 'border-red-500/40'}`}>
          <p className={message.type === 'success' ? 'text-emerald-400' : 'text-red-400'}>{message.text}</p>
          {message.type === 'success' && (
            <a href="/posts" className="mt-2 inline-block text-sm text-indigo-400 hover:underline">Go to Generated Posts →</a>
          )}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <h2 className="text-lg font-semibold">{editId ? 'Edit' : 'New'} Community</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            <input className="input" placeholder="Category (football, cricket, art...)" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required />
            <input className="input md:col-span-2" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <input className="input" placeholder="Tags (comma separated)" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
            <input className="input" placeholder="Blocked topics (comma separated)" value={form.blocked_topics} onChange={(e) => setForm({ ...form, blocked_topics: e.target.value })} />
            <input className="input" placeholder="Country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
            <select className="select" value={form.preferred_tone} onChange={(e) => setForm({ ...form, preferred_tone: e.target.value })}>
              <option value="friendly">Friendly</option>
              <option value="passionate">Passionate</option>
              <option value="professional">Professional</option>
              <option value="creative">Creative</option>
              <option value="playful">Playful</option>
            </select>
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_child_safe} onChange={(e) => setForm({ ...form, is_child_safe: e.target.checked })} /> Child Safe</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Active</label>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">{editId ? 'Update' : 'Create'}</button>
            <button type="button" onClick={resetForm} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--card-border)] text-left text-[var(--muted)]">
              <th className="px-6 py-3">Name</th>
              <th className="px-6 py-3">Category</th>
              <th className="px-6 py-3">Tone</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {communities.map((c) => (
              <tr key={c.id} className="table-row">
                <td className="px-6 py-4">
                  <p className="font-medium">{c.name}</p>
                  <p className="text-xs text-[var(--muted)]">{c.tags.slice(0, 3).join(', ')}</p>
                </td>
                <td className="px-6 py-4">{c.category}</td>
                <td className="px-6 py-4">{c.preferred_tone}</td>
                <td className="px-6 py-4">
                  <span className={`badge ${c.is_active ? 'badge-success' : 'badge-neutral'}`}>{c.is_active ? 'Active' : 'Inactive'}</span>
                  {c.is_child_safe && <span className="badge badge-info ml-1">Child Safe</span>}
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleGenerate(c.id, c.name)}
                      disabled={generatingId === c.id}
                      className="rounded p-1 hover:bg-indigo-600/20 disabled:opacity-50"
                      title="Generate Post"
                    >
                      <Sparkles className={`h-4 w-4 text-indigo-400 ${generatingId === c.id ? 'animate-pulse' : ''}`} />
                    </button>
                    <button onClick={() => handleEdit(c)} className="rounded p-1 hover:bg-white/10" title="Edit"><Pencil className="h-4 w-4" /></button>
                    <button onClick={() => handleDelete(c.id)} className="rounded p-1 hover:bg-red-500/20" title="Delete"><Trash2 className="h-4 w-4 text-red-400" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
