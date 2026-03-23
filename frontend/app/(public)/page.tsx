'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import {
  MessageSquare,
  Users,
  GitBranch,
  BarChart3,
  ArrowRight,
} from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/admin');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center">
        <div className="animate-pulse text-text-muted">Loading...</div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl text-center">
      {/* Hero */}
      <div className="mb-12">
        <h1 className="text-display text-text mb-3">EzMsg</h1>
        <p className="text-body text-text-secondary max-w-md mx-auto">
          Messaging protocol management for health interventions.
          Design, schedule, and monitor multi-step messaging flows.
        </p>
      </div>

      {/* Feature highlights */}
      <div className="grid grid-cols-2 gap-4 mb-12">
        <div className="card p-5 text-left">
          <MessageSquare className="h-5 w-5 text-accent mb-3" />
          <p className="text-body-sm font-medium text-text mb-1">Message Scheduling</p>
          <p className="text-caption text-text-muted">
            Automated delivery with retries, timing offsets, and variable substitution.
          </p>
        </div>
        <div className="card p-5 text-left">
          <GitBranch className="h-5 w-5 text-accent mb-3" />
          <p className="text-body-sm font-medium text-text mb-1">Protocol Editor</p>
          <p className="text-caption text-text-muted">
            Visual node graph editor for branching messaging workflows.
          </p>
        </div>
        <div className="card p-5 text-left">
          <Users className="h-5 w-5 text-accent mb-3" />
          <p className="text-body-sm font-medium text-text mb-1">Participant Tracking</p>
          <p className="text-caption text-text-muted">
            Enroll participants, track status, and manage variables per person.
          </p>
        </div>
        <div className="card p-5 text-left">
          <BarChart3 className="h-5 w-5 text-accent mb-3" />
          <p className="text-body-sm font-medium text-text mb-1">Analytics</p>
          <p className="text-caption text-text-muted">
            Delivery rates, queue health, and real-time scheduler monitoring.
          </p>
        </div>
      </div>

      {/* CTA */}
      <Link href="/login" className="btn-primary text-base px-8 py-3">
        Sign in to Dashboard
        <ArrowRight className="h-4 w-4" />
      </Link>

      {/* Footer */}
      <p className="mt-8 text-caption text-text-muted">
        Built for the QuitTxt Research Study
      </p>
    </div>
  );
}
