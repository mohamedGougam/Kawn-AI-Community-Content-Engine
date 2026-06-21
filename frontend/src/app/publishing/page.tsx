'use client';

import { useEffect, useState } from 'react';
import { api, PublishingJob, formatDate, statusBadge } from '@/lib/api';

export default function PublishingPage() {
  const [jobs, setJobs] = useState<PublishingJob[]>([]);

  useEffect(() => {
    api.getPublishingJobs().then(setJobs);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Publishing History</h1>
        <p className="text-[var(--muted)]">View scheduler jobs and publishing pipeline history</p>
      </div>

      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--card-border)] text-left text-[var(--muted)]">
              <th className="px-6 py-3">Job Type</th>
              <th className="px-6 py-3">Community</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Generated</th>
              <th className="px-6 py-3">Published</th>
              <th className="px-6 py-3">Blocked</th>
              <th className="px-6 py-3">Articles</th>
              <th className="px-6 py-3">Started</th>
              <th className="px-6 py-3">Completed</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id} className="table-row">
                <td className="px-6 py-4 font-medium">{j.job_type}</td>
                <td className="px-6 py-4">{j.community_name || 'All'}</td>
                <td className="px-6 py-4"><span className={`badge ${statusBadge(j.status)}`}>{j.status}</span></td>
                <td className="px-6 py-4">{j.posts_generated}</td>
                <td className="px-6 py-4 text-emerald-400">{j.posts_published}</td>
                <td className="px-6 py-4 text-red-400">{j.posts_blocked}</td>
                <td className="px-6 py-4">{j.articles_collected}</td>
                <td className="px-6 py-4 text-xs">{formatDate(j.started_at)}</td>
                <td className="px-6 py-4 text-xs">{formatDate(j.completed_at)}</td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr><td colSpan={9} className="px-6 py-8 text-center text-[var(--muted)]">No publishing jobs yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
