'use client';

import { useEffect, useState } from 'react';
import { ShieldAlert, Eye } from 'lucide-react';
import { api, Post, formatDate, formatPostType, statusBadge } from '@/lib/api';

export default function PostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState<Post | null>(null);
  const [page, setPage] = useState(1);

  const load = () => {
    api.getPosts({ page, status: statusFilter || undefined }).then((r) => {
      setPosts(r.items);
      setTotal(r.total);
    });
  };

  useEffect(() => { load(); }, [page, statusFilter]);

  const handleBlock = async (id: string) => {
    if (!confirm('Block this post?')) return;
    await api.blockPost(id, 'Blocked by admin');
    load();
    setSelected(null);
  };

  const handleReset = async () => {
    if (!confirm('Delete ALL posts, articles, analytics, and job history? Communities and sources will be kept.')) return;
    await api.resetContent();
    setSelected(null);
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Generated Posts</h1>
          <p className="text-[var(--muted)]">View AI-generated content, sources, and moderation results</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleReset} className="btn-secondary text-red-400">Clear all posts</button>
          <select className="select w-48" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="published">Published</option>
          <option value="blocked">Blocked</option>
          <option value="pending_moderation">Pending</option>
          <option value="draft">Draft</option>
        </select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--card-border)] text-left text-[var(--muted)]">
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Community</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {posts.map((p) => (
                <tr key={p.id} className="table-row">
                  <td className="max-w-xs truncate px-4 py-3 font-medium">{p.title}</td>
                  <td className="px-4 py-3">{p.community_name}</td>
                  <td className="px-4 py-3">{formatPostType(p.post_type)}</td>
                  <td className="px-4 py-3"><span className={`badge ${statusBadge(p.status)}`}>{p.status}</span></td>
                  <td className="px-4 py-3 text-xs">{formatDate(p.created_at)}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => setSelected(p)} className="rounded p-1 hover:bg-white/10"><Eye className="h-4 w-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between border-t border-[var(--card-border)] px-4 py-3">
            <span className="text-sm text-[var(--muted)]">{total} total posts</span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-secondary">Prev</button>
              <button disabled={posts.length < 20} onClick={() => setPage(page + 1)} className="btn-secondary">Next</button>
            </div>
          </div>
        </div>

        {selected && (
          <div className="card space-y-4">
            <h2 className="text-lg font-semibold">{selected.title}</h2>
            <div className="flex flex-wrap gap-2">
              <span className={`badge ${statusBadge(selected.status)}`}>{selected.status}</span>
              <span className="badge badge-info">{formatPostType(selected.post_type)}</span>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{selected.body}</p>
            {selected.poll_options && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-[var(--muted)]">Poll Options:</p>
                {selected.poll_options.map((o) => <p key={o} className="text-sm">• {o}</p>)}
              </div>
            )}
            {selected.sources.length > 0 && (
              <div>
                <p className="text-xs font-medium text-[var(--muted)]">Sources:</p>
                {selected.sources.map((s) => (
                  <p key={s.source_name} className="text-sm text-cyan-400">{s.source_name}</p>
                ))}
              </div>
            )}
            {selected.moderation && (
              <div className="rounded-lg border border-[var(--card-border)] p-3">
                <p className="text-xs font-medium text-[var(--muted)]">Moderation</p>
                <p className="text-sm">Safe: {selected.moderation.is_safe ? 'Yes' : 'No'} · Score: {selected.moderation.overall_score}</p>
                {selected.moderation.flags.length > 0 && (
                  <p className="text-xs text-red-400">Flags: {selected.moderation.flags.join(', ')}</p>
                )}
              </div>
            )}
            {selected.status !== 'blocked' && (
              <button onClick={() => handleBlock(selected.id)} className="btn-secondary flex items-center gap-2 text-red-400">
                <ShieldAlert className="h-4 w-4" /> Block Post
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
