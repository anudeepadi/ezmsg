'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { projects, scheduler, Project, ProjectListResponse, QueueHealth, ApiError } from '@/lib/api';
import { formatRelativeTime, getStatusVariant, cn } from '@/lib/utils';
import {
  FolderKanban,
  Users,
  MessageSquare,
  Clock,
  ArrowRight,
  AlertTriangle,
} from 'lucide-react';

export default function DashboardPage() {
  const [projectList, setProjectList] = useState<Project[]>([]);
  const [queueHealth, setQueueHealth] = useState<QueueHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [projectsResponse, healthData] = await Promise.all([
          projects.list(),
          scheduler.health(),
        ]);
        setProjectList(projectsResponse.items);
        setQueueHealth(healthData);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="p-6">
          <div className="animate-pulse space-y-6">
            <div className="grid grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-surface rounded-lg" />
              ))}
            </div>
            <div className="h-64 bg-surface rounded-lg" />
          </div>
        </div>
      </>
    );
  }

  const activeProjects = projectList.filter((p) => p.status === 'ACTIVE');
  const totalParticipants = projectList.reduce(
    (sum, p) => sum + (p.participant_count || 0),
    0
  );

  return (
    <>
      <Header title="Dashboard" description="Overview of your messaging protocols" />

      <div className="p-6 space-y-6">
        {error && (
          <div className="p-4 bg-error-light text-error rounded-lg flex items-center gap-3">
            <AlertTriangle className="h-5 w-5" />
            {error}
          </div>
        )}

        {/* Stats grid */}
        <div className="grid grid-cols-4 gap-6">
          <StatCard
            label="Total Projects"
            value={projectList.length}
            subValue={`${activeProjects.length} active`}
            icon={FolderKanban}
          />
          <StatCard
            label="Participants"
            value={totalParticipants}
            subValue="across all projects"
            icon={Users}
          />
          <StatCard
            label="Messages Sent Today"
            value={queueHealth?.sent_today || 0}
            subValue={`${queueHealth?.pending_count || 0} pending`}
            icon={MessageSquare}
          />
          <StatCard
            label="Queue Health"
            value={queueHealth?.failed_count || 0}
            subValue="failed messages"
            icon={Clock}
            variant={queueHealth?.failed_count ? 'warning' : 'default'}
          />
        </div>

        {/* Projects list */}
        <div className="card">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h2 className="text-subtitle text-text">Recent Projects</h2>
            <Link href="/admin/projects" className="btn-ghost text-accent">
              View all
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {projectList.length === 0 ? (
            <div className="p-8 text-center">
              <FolderKanban className="h-12 w-12 text-text-muted mx-auto mb-4" />
              <p className="text-body text-text-secondary mb-4">No projects yet</p>
              <Link href="/admin/projects/new" className="btn-primary">
                Create your first project
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {projectList.slice(0, 5).map((project) => (
                <Link
                  key={project.id}
                  href={`/admin/projects/${project.id}`}
                  className="flex items-center p-4 hover:bg-background transition-colors"
                >
                  <div className="flex-1">
                    <h3 className="text-body font-medium text-text">
                      {project.name}
                    </h3>
                    <p className="text-body-sm text-text-secondary">
                      {project.uu_id || `ID: ${project.id}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-body-sm text-text">
                        {project.participant_count || 0} participants
                      </p>
                      <p className="text-caption text-text-muted">
                        {project.node_count || 0} nodes
                      </p>
                    </div>
                    <span
                      className={cn('badge', {
                        'badge-success': getStatusVariant(project.status) === 'success',
                        'badge-warning': getStatusVariant(project.status) === 'warning',
                        'badge-error': getStatusVariant(project.status) === 'error',
                        'badge-default': getStatusVariant(project.status) === 'default',
                      })}
                    >
                      {project.status}
                    </span>
                    <ArrowRight className="h-5 w-5 text-text-muted" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Queue status */}
        {queueHealth && (
          <div className="card">
            <div className="p-4 border-b border-border">
              <h2 className="text-subtitle text-text">Scheduler Status</h2>
            </div>
            <div className="p-4 grid grid-cols-5 gap-4">
              <div>
                <p className="text-caption text-text-muted mb-1">Pending</p>
                <p className="text-title text-text">{queueHealth.pending_count}</p>
              </div>
              <div>
                <p className="text-caption text-text-muted mb-1">In Progress</p>
                <p className="text-title text-text">{queueHealth.in_progress_count}</p>
              </div>
              <div>
                <p className="text-caption text-text-muted mb-1">Sent Today</p>
                <p className="text-title text-success">{queueHealth.sent_today}</p>
              </div>
              <div>
                <p className="text-caption text-text-muted mb-1">Failed</p>
                <p
                  className={cn('text-title', {
                    'text-error': queueHealth.failed_count > 0,
                    'text-text': queueHealth.failed_count === 0,
                  })}
                >
                  {queueHealth.failed_count}
                </p>
              </div>
              <div>
                <p className="text-caption text-text-muted mb-1">Oldest Pending</p>
                <p className="text-title text-text">
                  {queueHealth.oldest_pending_minutes
                    ? `${Math.round(queueHealth.oldest_pending_minutes)}m`
                    : '-'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  subValue: string;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'warning' | 'success' | 'error';
}

function StatCard({ label, value, subValue, icon: Icon, variant = 'default' }: StatCardProps) {
  return (
    <div className="card p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-body-sm text-text-secondary mb-1">{label}</p>
          <p
            className={cn('text-display', {
              'text-text': variant === 'default',
              'text-warning': variant === 'warning',
              'text-success': variant === 'success',
              'text-error': variant === 'error',
            })}
          >
            {value.toLocaleString()}
          </p>
          <p className="text-caption text-text-muted mt-1">{subValue}</p>
        </div>
        <div
          className={cn('p-3 rounded-lg', {
            'bg-background': variant === 'default',
            'bg-warning-light': variant === 'warning',
            'bg-success-light': variant === 'success',
            'bg-error-light': variant === 'error',
          })}
        >
          <Icon
            className={cn('h-6 w-6', {
              'text-text-muted': variant === 'default',
              'text-warning': variant === 'warning',
              'text-success': variant === 'success',
              'text-error': variant === 'error',
            })}
          />
        </div>
      </div>
    </div>
  );
}
