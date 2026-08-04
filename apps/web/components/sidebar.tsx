'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Building2, ListChecks, Mail, Send } from 'lucide-react';
import type { ComponentType } from 'react';

interface NavItem {
  href: string;
  label: string;
  icon: ComponentType<{ size?: number; strokeWidth?: number }>;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/empresas', label: 'Empresas', icon: Building2 },
  { href: '/listas', label: 'Listas', icon: ListChecks },
  { href: '/campanhas', label: 'Campanhas', icon: Send },
  { href: '/config/email', label: 'Config. de e-mail', icon: Mail },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-zinc-200 bg-white">
      <div className="flex items-center gap-2 px-5 py-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-600 text-sm font-bold text-white">
          R
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-zinc-900">Radar CNPJ</span>
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active ? 'bg-brand-50 text-brand-700' : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900'
              }`}
            >
              {active && <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-brand-600" />}
              <Icon size={17} strokeWidth={2} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-100 px-5 py-4 text-xs text-zinc-400">
        Radar &middot; uso interno
      </div>
    </aside>
  );
}
