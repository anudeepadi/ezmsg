'use client';

import { AuthGuard, Sidebar, Toasts } from '@/components/layout';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main className="ml-64 min-h-screen">
          {children}
        </main>
        <Toasts />
      </div>
    </AuthGuard>
  );
}
