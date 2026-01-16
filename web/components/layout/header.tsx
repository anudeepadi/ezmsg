'use client';

import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

interface HeaderProps {
  title?: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Header({ title, description, actions }: HeaderProps) {
  const pathname = usePathname();

  // Auto-generate title from pathname if not provided
  const autoTitle = title || getPageTitle(pathname);

  return (
    <header className="h-16 border-b border-border bg-surface flex items-center px-6">
      <div className="flex-1">
        <h1 className="text-title text-text">{autoTitle}</h1>
        {description && (
          <p className="text-body-sm text-text-secondary mt-0.5">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </header>
  );
}

function getPageTitle(pathname: string): string {
  const segments = pathname.split('/').filter(Boolean);

  if (segments.length === 1 && segments[0] === 'admin') {
    return 'Dashboard';
  }

  const lastSegment = segments[segments.length - 1];

  // Handle specific pages
  const titleMap: Record<string, string> = {
    projects: 'Projects',
    participants: 'Participants',
    templates: 'Templates',
    nodes: 'Messaging Nodes',
    variables: 'Variables',
    analytics: 'Analytics',
    scheduler: 'Scheduler',
    settings: 'Settings',
    new: 'Create New',
  };

  return titleMap[lastSegment] || capitalize(lastSegment);
}

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
