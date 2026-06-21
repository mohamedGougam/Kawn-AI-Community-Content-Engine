const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `API error: ${res.status}`);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

export interface Community {
  id: string;
  name: string;
  description: string | null;
  category: string;
  tags: string[];
  blocked_topics: string[];
  language: string;
  country: string | null;
  region: string | null;
  preferred_tone: string;
  posts_per_day: number;
  publishing_frequency: string;
  is_active: boolean;
  is_child_safe: boolean;
  created_at: string;
  updated_at: string;
}

export interface Source {
  id: string;
  name: string;
  source_type: string;
  url: string;
  category: string | null;
  is_active: boolean;
  reliability_score: number;
  fetch_interval_minutes: number;
  last_fetched_at: string | null;
}

export interface Post {
  id: string;
  community_id: string;
  community_name: string | null;
  title: string;
  body: string;
  post_type: string;
  tone: string;
  hashtags: string[];
  poll_options: string[] | null;
  status: string;
  sources: { source_name: string; source_url: string | null }[];
  moderation: {
    is_safe: boolean;
    overall_score: number;
    checks: Record<string, boolean>;
    flags: string[];
    reason: string | null;
  } | null;
  published_at: string | null;
  created_at: string;
}

export interface AnalyticsOverview {
  total_communities: number;
  active_communities: number;
  total_generated_posts: number;
  total_published_posts: number;
  total_blocked_posts: number;
  total_failed_posts: number;
  active_sources: number;
  ai_provider_status: Record<string, { available: boolean; has_api_key: boolean; active: boolean }>;
  post_type_breakdown: Record<string, number>;
  top_communities: { name: string; posts: number }[];
  recent_activity: { title: string; status: string; created_at: string; community: string }[];
}

export interface PublishingJob {
  id: string;
  community_id: string | null;
  community_name: string | null;
  job_type: string;
  status: string;
  posts_generated: number;
  posts_published: number;
  posts_blocked: number;
  posts_failed: number;
  articles_collected: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface AISetting {
  id: string;
  provider: string;
  is_active: boolean;
  is_default: boolean;
  model: string | null;
  temperature: number;
  max_tokens: number;
  has_api_key: boolean;
}

export interface SourceMapping {
  community_id: string;
  community_name: string;
  category: string;
  tags: string[];
  sources: {
    id: string;
    name: string;
    category: string | null;
    source_type: string;
    last_fetched_at: string | null;
    is_active: boolean;
  }[];
}

export const api = {
  getHealth: () => fetchApi<{ status: string; scheduler_running: boolean; ai_provider: string }>('/api/health'),
  getCommunities: () => fetchApi<Community[]>('/api/communities'),
  createCommunity: (data: Partial<Community>) => fetchApi<Community>('/api/communities', { method: 'POST', body: JSON.stringify(data) }),
  updateCommunity: (id: string, data: Partial<Community>) => fetchApi<Community>(`/api/communities/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCommunity: (id: string) => fetchApi<void>(`/api/communities/${id}`, { method: 'DELETE' }),
  getSources: () => fetchApi<Source[]>('/api/sources'),
  getSourceMapping: () => fetchApi<SourceMapping[]>('/api/sources/mapping'),
  createSource: (data: Partial<Source>) => fetchApi<Source>('/api/sources', { method: 'POST', body: JSON.stringify(data) }),
  updateSource: (id: string, data: Partial<Source>) => fetchApi<Source>(`/api/sources/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSource: (id: string) => fetchApi<void>(`/api/sources/${id}`, { method: 'DELETE' }),
  getPosts: (params?: { page?: number; status?: string; community_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set('page', String(params.page));
    if (params?.status) q.set('status', params.status);
    if (params?.community_id) q.set('community_id', params.community_id);
    return fetchApi<{ items: Post[]; total: number; page: number; page_size: number }>(`/api/posts?${q}`);
  },
  generatePost: (community_id: string, post_type?: string) =>
    fetchApi<Post>('/api/posts/generate', { method: 'POST', body: JSON.stringify({ community_id, post_type }) }),
  blockPost: (post_id: string, reason?: string) =>
    fetchApi<Post>('/api/posts/block', { method: 'POST', body: JSON.stringify({ post_id, reason }) }),
  getPublishingJobs: () => fetchApi<PublishingJob[]>('/api/posts/jobs'),
  resetContent: () => fetchApi<{ message: string; deleted: Record<string, number> }>('/api/admin/reset-content', { method: 'POST' }),
  getAnalytics: () => fetchApi<AnalyticsOverview>('/api/analytics'),
  getCommunityAnalytics: (id: string) => fetchApi<Record<string, unknown>>(`/api/analytics/community/${id}`),
  getAISettings: () => fetchApi<AISetting[]>('/api/settings/ai'),
  updateAISetting: (provider: string, data: Partial<AISetting>) =>
    fetchApi<AISetting>(`/api/settings/ai/${provider}`, { method: 'POST', body: JSON.stringify(data) }),
};

export function statusBadge(status: string) {
  const map: Record<string, string> = {
    published: 'badge-success',
    approved: 'badge-success',
    blocked: 'badge-danger',
    failed: 'badge-danger',
    draft: 'badge-neutral',
    pending_moderation: 'badge-warning',
    completed: 'badge-success',
    running: 'badge-info',
    failed_job: 'badge-danger',
  };
  return map[status] || 'badge-neutral';
}

export function formatDate(d: string | null) {
  if (!d) return '—';
  return new Date(d).toLocaleString();
}

export function formatPostType(t: string) {
  return t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
