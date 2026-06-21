'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  Rss,
  FileText,
  History,
  BarChart3,
  Settings,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';

const nav = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/communities', label: 'Communities', icon: Users },
  { href: '/sources', label: 'Sources', icon: Rss },
  { href: '/posts', label: 'Generated Posts', icon: FileText },
  { href: '/publishing', label: 'Publishing History', icon: History },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/settings', label: 'AI Configuration', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-[var(--card-border)] bg-[var(--card)]">
      <div className="flex items-center gap-3 border-b border-[var(--card-border)] px-6 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white">Kawn AI</h1>
          <p className="text-xs text-[var(--muted)]">Content Engine</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition',
                active
                  ? 'bg-indigo-600/20 text-indigo-400'
                  : 'text-[var(--muted)] hover:bg-white/5 hover:text-white'
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[var(--card-border)] p-4">
        <p className="text-xs text-[var(--muted)]">Kawn Community Content Engine v1.0</p>
      </div>
    </aside>
  );
}
