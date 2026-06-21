'use client';

import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { api, AnalyticsOverview } from '@/lib/api';

const COLORS = ['#6366f1', '#22d3ee', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#fb923c', '#2dd4bf'];

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);

  useEffect(() => {
    api.getAnalytics().then(setData);
  }, []);

  if (!data) return <div className="text-[var(--muted)]">Loading analytics...</div>;

  const postTypeData = Object.entries(data.post_type_breakdown).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value,
  }));

  const statusData = [
    { name: 'Published', value: data.total_published_posts },
    { name: 'Blocked', value: data.total_blocked_posts },
    { name: 'Failed', value: data.total_failed_posts },
    { name: 'Other', value: Math.max(0, data.total_generated_posts - data.total_published_posts - data.total_blocked_posts - data.total_failed_posts) },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Analytics</h1>
        <p className="text-[var(--muted)]">Content generation metrics and community insights</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: 'Communities', value: data.total_communities },
          { label: 'Generated', value: data.total_generated_posts },
          { label: 'Published', value: data.total_published_posts },
          { label: 'Blocked', value: data.total_blocked_posts },
        ].map((s) => (
          <div key={s.label} className="card text-center">
            <p className="text-sm text-[var(--muted)]">{s.label}</p>
            <p className="text-3xl font-bold">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Post Types</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={postTypeData}>
              <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
              <YAxis tick={{ fill: '#9ca3af' }} />
              <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2a2f3d' }} />
              <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Post Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                {statusData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2a2f3d' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-4 text-lg font-semibold">Top Communities by Posts</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.top_communities} layout="vertical">
            <XAxis type="number" tick={{ fill: '#9ca3af' }} />
            <YAxis dataKey="name" type="category" tick={{ fill: '#9ca3af', fontSize: 11 }} width={180} />
            <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2a2f3d' }} />
            <Bar dataKey="posts" fill="#22d3ee" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h2 className="mb-4 text-lg font-semibold">AI Provider Status</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {Object.entries(data.ai_provider_status).map(([name, status]) => (
            <div key={name} className="rounded-lg border border-[var(--card-border)] p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium capitalize">{name}</span>
                {status.active && <span className="badge badge-success">Active</span>}
              </div>
              <p className="mt-1 text-xs text-[var(--muted)]">
                API Key: {status.has_api_key ? 'Configured' : 'Not set'}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
