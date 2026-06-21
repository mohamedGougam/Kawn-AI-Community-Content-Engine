'use client';

import { useEffect, useState } from 'react';
import { Users, FileText, CheckCircle, ShieldAlert, Rss, Bot, Activity } from 'lucide-react';
import { api, AnalyticsOverview, formatDate, statusBadge } from '@/lib/api';

function StatCard({ label, value, icon: Icon, color }: { label: string; value: number | string; icon: React.ElementType; color: string }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${color}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div>
        <p className="text-sm text-[var(--muted)]">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [health, setHealth] = useState<{ scheduler_running: boolean; ai_provider: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getAnalytics(), api.getHealth()])
      .then(([analytics, h]) => {
        setData(analytics);
        setHealth(h);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="card border-red-500/30">
        <p className="text-red-400">Failed to load dashboard: {error}</p>
        <p className="mt-2 text-sm text-[var(--muted)]">Ensure the backend is running at http://localhost:8000</p>
      </div>
    );
  }

  if (!data) {
    return <div className="flex h-64 items-center justify-center text-[var(--muted)]">Loading dashboard...</div>;
  }

  const activeProvider = Object.entries(data.ai_provider_status).find(([, v]) => v.active)?.[0] || 'mock';

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="mt-1 text-[var(--muted)]">Overview of your AI content generation engine</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <StatCard label="Total Communities" value={data.total_communities} icon={Users} color="bg-indigo-600" />
        <StatCard label="Generated Posts" value={data.total_generated_posts} icon={FileText} color="bg-cyan-600" />
        <StatCard label="Published Posts" value={data.total_published_posts} icon={CheckCircle} color="bg-emerald-600" />
        <StatCard label="Blocked Posts" value={data.total_blocked_posts} icon={ShieldAlert} color="bg-red-600" />
        <StatCard label="Active Sources" value={data.active_sources} icon={Rss} color="bg-amber-600" />
        <StatCard label="AI Provider" value={activeProvider} icon={Bot} color="bg-purple-600" />
        <StatCard label="Scheduler" value={health?.scheduler_running ? 'Running' : 'Stopped'} icon={Activity} color="bg-blue-600" />
        <StatCard label="Active Communities" value={data.active_communities} icon={Users} color="bg-teal-600" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Top Communities</h2>
          <div className="space-y-3">
            {data.top_communities.map((c, i) => (
              <div key={c.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600/20 text-xs font-bold text-indigo-400">
                    {i + 1}
                  </span>
                  <span className="text-sm">{c.name}</span>
                </div>
                <span className="text-sm text-[var(--muted)]">{c.posts} posts</span>
              </div>
            ))}
            {data.top_communities.length === 0 && <p className="text-sm text-[var(--muted)]">No data yet</p>}
          </div>
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Recent Activity</h2>
          <div className="space-y-3">
            {data.recent_activity.map((a, i) => (
              <div key={i} className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{a.title}</p>
                  <p className="text-xs text-[var(--muted)]">{a.community} · {formatDate(a.created_at)}</p>
                </div>
                <span className={`badge ${statusBadge(a.status)}`}>{a.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-4 text-lg font-semibold">Post Type Breakdown</h2>
        <div className="flex flex-wrap gap-3">
          {Object.entries(data.post_type_breakdown).map(([type, count]) => (
            <div key={type} className="rounded-lg border border-[var(--card-border)] px-4 py-2">
              <p className="text-xs text-[var(--muted)]">{type.replace(/_/g, ' ')}</p>
              <p className="text-lg font-bold">{count}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
