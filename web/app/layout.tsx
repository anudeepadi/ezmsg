import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EzMsg - Messaging Protocol Management',
  description: 'Manage messaging protocols for health interventions',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
