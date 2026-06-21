'use client';

import { useEffect, useState } from 'react';
import { Check, Key } from 'lucide-react';
import { api, AISetting } from '@/lib/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState<AISetting[]>([]);
  const [saving, setSaving] = useState<string | null>(null);

  const load = () => api.getAISettings().then(setSettings);
  useEffect(() => { load(); }, []);

  const handleActivate = async (provider: string) => {
    setSaving(provider);
    await api.updateAISetting(provider, { is_active: true, is_default: true });
    for (const s of settings) {
      if (s.provider !== provider && s.is_default) {
        await api.updateAISetting(s.provider, { is_default: false });
      }
    }
    await load();
    setSaving(null);
  };

  const handleUpdate = async (provider: string, field: string, value: number) => {
    await api.updateAISetting(provider, { [field]: value });
    load();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">AI Configuration</h1>
        <p className="text-[var(--muted)]">Manage AI providers, models, and safety settings</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {settings.map((s) => (
          <div key={s.provider} className={`card ${s.is_default ? 'border-indigo-500/50' : ''}`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold capitalize">{s.provider}</h3>
                <p className="text-sm text-[var(--muted)]">Model: {s.model || 'Default'}</p>
              </div>
              <div className="flex items-center gap-2">
                {s.has_api_key ? (
                  <span className="badge badge-success flex items-center gap-1"><Key className="h-3 w-3" /> Key Set</span>
                ) : (
                  <span className="badge badge-neutral">No Key</span>
                )}
                {s.is_default && <span className="badge badge-info">Default</span>}
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <label className="text-xs text-[var(--muted)]">Temperature: {s.temperature}</label>
                <input
                  type="range" min="0" max="1" step="0.1"
                  value={Number(s.temperature)}
                  onChange={(e) => handleUpdate(s.provider, 'temperature', parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-xs text-[var(--muted)]">Max Tokens: {s.max_tokens}</label>
                <input
                  type="range" min="256" max="4096" step="256"
                  value={s.max_tokens}
                  onChange={(e) => handleUpdate(s.provider, 'max_tokens', parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>

            {!s.is_default && (
              <button
                onClick={() => handleActivate(s.provider)}
                disabled={saving === s.provider}
                className="btn-primary mt-4 flex items-center gap-2"
              >
                <Check className="h-4 w-4" />
                {saving === s.provider ? 'Activating...' : 'Set as Default'}
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <h2 className="mb-3 text-lg font-semibold">Environment Variables</h2>
        <p className="mb-4 text-sm text-[var(--muted)]">
          Configure API keys in your <code className="rounded bg-white/5 px-1">.env</code> file. The mock provider works without any keys.
        </p>
        <div className="grid grid-cols-1 gap-2 font-mono text-xs md:grid-cols-2">
          {['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'HUGGINGFACE_API_KEY', 'NEWS_API_KEY', 'AI_DEFAULT_PROVIDER'].map((v) => (
            <div key={v} className="rounded bg-white/5 px-3 py-2">{v}</div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 text-lg font-semibold">Safety Settings</h2>
        <p className="text-sm text-[var(--muted)]">
          All generated content passes through AI moderation checking for hate speech, harassment, racism,
          misinformation, spam, political extremism, child safety, profanity, adult content, and violence.
          Unsafe content is automatically blocked and visible in the admin portal.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {['Hate Speech', 'Harassment', 'Racism', 'Misinformation', 'Spam', 'Extremism', 'Child Safety', 'Profanity', 'Adult Content', 'Violence'].map((c) => (
            <span key={c} className="badge badge-success">{c}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
