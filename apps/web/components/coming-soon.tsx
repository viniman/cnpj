import type { ComponentType } from 'react';

export function ComingSoon({
  icon: Icon,
  title,
  description,
}: {
  icon: ComponentType<{ size?: number; strokeWidth?: number }>;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-zinc-200 bg-white px-8 py-20 text-center">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-50 text-brand-600">
        <Icon size={20} strokeWidth={2} />
      </div>
      <h2 className="text-sm font-semibold text-zinc-900">{title}</h2>
      <p className="max-w-sm text-sm text-zinc-500">{description}</p>
    </div>
  );
}
