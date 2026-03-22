'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import {
  projects,
  analytics,
  Project,
  OverviewStats,
  ApiError,
} from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { formatDate, getStatusVariant, cn } from '@/lib/utils';
import {
  ArrowLeft,
  Users,
  FileText,
  GitBranch,
  Variable,
  BarChart3,
  Settings,
  ArrowRight,
  MessageSquare,
  CheckCircle,
  Clock,
  AlertTriangle,
  Timer,
  PlayCircle,
  MessageCircle,
} from 'lucide-react';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [projectData, statsData] = await Promise.all([
          projects.get(projectId),
          analytics.overview(projectId),
        ]);
        setProject(projectData);
        setStats(statsData);
      } catch (err) {
        addToast('error', 'Failed to load project');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [projectId, addToast]);

  if (loading) {
    return (
      <>
        <Header title="Loading..." />
        <div className="p-6">
          <div className="animate-pulse space-y-6">
            <div className="h-32 bg-surface rounded-lg" />
            <div className="grid grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 bg-surface rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </>
    );
  }

  if (!project) {
    return (
      <>
        <Header title="Project Not Found" />
        <div className="p-6">
          <div className="card p-8 text-center">
            <p className="text-body text-text-secondary mb-4">
              The project you're looking for doesn't exist or you don't have access.
            </p>
            <Link href="/admin/projects" className="btn-primary">
              Back to Projects
            </Link>
          </div>
        </div>
      </>
    );
  }

  const quickLinks = [
    {
      name: 'Participants',
      href: `/admin/projects/${projectId}/participants`,
      icon: Users,
      count: stats?.total_participants,
    },
    {
      name: 'Templates',
      href: `/admin/projects/${projectId}/templates`,
      icon: FileText,
      count: null,
    },
    {
      name: 'Nodes',
      href: `/admin/projects/${projectId}/nodes`,
      icon: GitBranch,
      count: project.node_count,
    },
    {
      name: 'Variables',
      href: `/admin/projects/${projectId}/variables`,
      icon: Variable,
      count: null,
    },
    {
      name: 'Scheduler',
      href: `/admin/projects/${projectId}/scheduler`,
      icon: Timer,
      count: null,
    },
    {
      name: 'Analytics',
      href: `/admin/projects/${projectId}/analytics`,
      icon: BarChart3,
      count: null,
    },
    {
      name: 'Test Protocol',
      href: `/admin/projects/${projectId}/test-protocol`,
      icon: PlayCircle,
      count: null,
    },
    {
      name: 'Simulator',
      href: `/admin/projects/${projectId}/simulator`,
      icon: MessageCircle,
      count: null,
    },
  ];

  return (
    <>
      <Header
        title={project.name}
        description={project.description || `Project UUID: ${project.uu_id || project.id}`}
        actions={
          <div className="flex items-center gap-3">
            <Link href="/admin/projects" className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <Link
              href={`/admin/projects/${projectId}/edit`}
              className="btn-secondary"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Project info card */}
        <div className="card p-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
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
                {project.uu_id && (
                  <code className="text-body-sm font-mono bg-background px-2 py-0.5 rounded">
                    {project.uu_id}
                  </code>
                )}
              </div>
              <p className="text-body-sm text-text-secondary">
                Owner: {project.owner_email}
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-4 gap-6">
            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-accent-light rounded-lg">
                  <Users className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <p className="text-caption text-text-muted">Total Participants</p>
                  <p className="text-title text-text">{stats.total_participants}</p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-success-light rounded-lg">
                  <CheckCircle className="h-5 w-5 text-success" />
                </div>
                <div>
                  <p className="text-caption text-text-muted">Active</p>
                  <p className="text-title text-text">{stats.active_participants}</p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-background rounded-lg">
                  <MessageSquare className="h-5 w-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-caption text-text-muted">Messages Sent</p>
                  <p className="text-title text-text">{stats.total_messages_sent}</p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div
                  className={cn('p-2.5 rounded-lg', {
                    'bg-success-light': stats.delivery_rate >= 95,
                    'bg-warning-light': stats.delivery_rate >= 80 && stats.delivery_rate < 95,
                    'bg-error-light': stats.delivery_rate < 80,
                  })}
                >
                  {stats.delivery_rate >= 95 ? (
                    <CheckCircle className="h-5 w-5 text-success" />
                  ) : stats.delivery_rate >= 80 ? (
                    <Clock className="h-5 w-5 text-warning" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-error" />
                  )}
                </div>
                <div>
                  <p className="text-caption text-text-muted">Delivery Rate</p>
                  <p className="text-title text-text">{stats.delivery_rate}%</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick links */}
        <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
          {quickLinks.map((link) => {
            const Icon = link.icon;
            return (
              <Link
                key={link.name}
                href={link.href}
                className="card p-5 hover:shadow-elevated transition-shadow group"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2 bg-background rounded-lg group-hover:bg-accent-light transition-colors">
                    <Icon className="h-5 w-5 text-text-muted group-hover:text-accent transition-colors" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-text-muted group-hover:text-accent transition-colors" />
                </div>
                <p className="text-body font-medium text-text">{link.name}</p>
                {link.count !== null && link.count !== undefined && (
                  <p className="text-caption text-text-muted">{link.count} items</p>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </>
  );
}
