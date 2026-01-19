'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { scheduler, QueueHealth, ScheduledMessage, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  RefreshCw,
  Clock,
  AlertCircle,
  CheckCircle2,
  Send,
  Play,
  Pause,
  RotateCcw,
  XCircle,
  Timer,
  TrendingUp,
  Loader2,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

type TabType = 'overview' | 'pending' | 'failed';

export default function SchedulerPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [health, setHealth] = useState<QueueHealth | null>(null);
  const [pendingMessages, setPendingMessages] = useState<ScheduledMessage[]>([]);
  const [failedMessages, setFailedMessages] = useState<ScheduledMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      const [healthData, pending, failed] = await Promise.all([
        scheduler.health(),
        scheduler.pending(projectId, 100),
        scheduler.failed(projectId, 100),
      ]);
      setHealth(healthData);
      setPendingMessages(pending);
      setFailedMessages(failed);
    } catch (err) {
      if (!silent) {
        addToast('error', 'Failed to load scheduler data');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [projectId, addToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadData]);

  async function handleRequeue() {
    if (!confirm('Requeue all failed messages from the last 24 hours?')) return;

    try {
      const result = await scheduler.requeue(24);
      addToast('success', result.message);
      loadData(true);
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to requeue messages');
    }
  }

  async function handleAbortProject() {
    if (!confirm('Abort ALL pending messages for this project? This cannot be undone.')) return;

    try {
      const result = await scheduler.abortProject(projectId);
      addToast('success', result.message);
      loadData(true);
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to abort messages');
    }
  }

  const getHealthStatus = () => {
    if (!health) return 'unknown';
    if (health.failed_count > 10) return 'critical';
    if (health.failed_count > 0 || (health.oldest_pending_minutes && health.oldest_pending_minutes > 30)) return 'warning';
    return 'healthy';
  };

  const healthStatus = getHealthStatus();

  return (
    <>
      <Header
        title="Message Scheduler"
        description="Monitor and manage scheduled message delivery"
        actions={
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={cn('btn-ghost', autoRefresh && 'text-success')}
              title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
            >
              {autoRefresh ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            </button>
            <button
              onClick={() => loadData(true)}
              disabled={refreshing}
              className="btn-secondary"
            >
              <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
              Refresh
            </button>
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </div>
        }
      />

      <div className="p-6">
        {loading ? (
          <div className="card p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-accent" />
            <p className="mt-2 text-text-muted">Loading scheduler data...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Health Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Status Card */}
              <div
                className={cn(
                  'card p-4 border-l-4',
                  healthStatus === 'healthy' && 'border-l-success',
                  healthStatus === 'warning' && 'border-l-warning',
                  healthStatus === 'critical' && 'border-l-error'
                )}
              >
                <div className="flex items-center gap-3">
                  {healthStatus === 'healthy' && <CheckCircle2 className="h-8 w-8 text-success" />}
                  {healthStatus === 'warning' && <AlertCircle className="h-8 w-8 text-warning" />}
                  {healthStatus === 'critical' && <XCircle className="h-8 w-8 text-error" />}
                  <div>
                    <p className="text-caption text-text-muted">Status</p>
                    <p className="text-title text-text capitalize">{healthStatus}</p>
                  </div>
                </div>
              </div>

              {/* Pending Count */}
              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-accent/10 rounded-lg">
                    <Clock className="h-6 w-6 text-accent" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Pending</p>
                    <p className="text-title text-text">{health?.pending_count || 0}</p>
                  </div>
                </div>
              </div>

              {/* In Progress */}
              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-warning/10 rounded-lg">
                    <Loader2 className="h-6 w-6 text-warning" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">In Progress</p>
                    <p className="text-title text-text">{health?.in_progress_count || 0}</p>
                  </div>
                </div>
              </div>

              {/* Failed */}
              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-error/10 rounded-lg">
                    <AlertCircle className="h-6 w-6 text-error" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Failed</p>
                    <p className="text-title text-text">{health?.failed_count || 0}</p>
                  </div>
                </div>
              </div>

              {/* Sent Today */}
              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-success/10 rounded-lg">
                    <Send className="h-6 w-6 text-success" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Sent Today</p>
                    <p className="text-title text-text">{health?.sent_today || 0}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Oldest Pending Warning */}
            {health?.oldest_pending_minutes && health.oldest_pending_minutes > 5 && (
              <div
                className={cn(
                  'p-4 rounded-lg flex items-center gap-3',
                  health.oldest_pending_minutes > 30 ? 'bg-error/10 text-error' : 'bg-warning/10 text-warning'
                )}
              >
                <Timer className="h-5 w-5" />
                <p>
                  Oldest pending message is <strong>{Math.round(health.oldest_pending_minutes)}</strong> minutes overdue.
                  {health.oldest_pending_minutes > 30 && ' Check worker status.'}
                </p>
              </div>
            )}

            {/* Tabs */}
            <div className="flex gap-1 border-b border-border">
              <button
                onClick={() => setActiveTab('overview')}
                className={cn(
                  'px-4 py-2 text-body-sm font-medium border-b-2 transition-colors',
                  activeTab === 'overview'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-text-muted hover:text-text'
                )}
              >
                <TrendingUp className="h-4 w-4 inline mr-1.5" />
                Overview
              </button>
              <button
                onClick={() => setActiveTab('pending')}
                className={cn(
                  'px-4 py-2 text-body-sm font-medium border-b-2 transition-colors',
                  activeTab === 'pending'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-text-muted hover:text-text'
                )}
              >
                <Clock className="h-4 w-4 inline mr-1.5" />
                Pending ({pendingMessages.length})
              </button>
              <button
                onClick={() => setActiveTab('failed')}
                className={cn(
                  'px-4 py-2 text-body-sm font-medium border-b-2 transition-colors',
                  activeTab === 'failed'
                    ? 'border-accent text-accent'
                    : 'border-transparent text-text-muted hover:text-text'
                )}
              >
                <AlertCircle className="h-4 w-4 inline mr-1.5" />
                Failed ({failedMessages.length})
              </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Actions Panel */}
                <div className="card p-6">
                  <h3 className="text-title text-text mb-4">Actions</h3>
                  <div className="space-y-3">
                    <button
                      onClick={handleRequeue}
                      disabled={!health?.failed_count}
                      className="btn-secondary w-full justify-start"
                    >
                      <RotateCcw className="h-4 w-4" />
                      Requeue Failed Messages
                      {health?.failed_count ? ` (${health.failed_count})` : ''}
                    </button>
                    <button
                      onClick={handleAbortProject}
                      disabled={!health?.pending_count}
                      className="btn-ghost w-full justify-start text-error hover:bg-error/10"
                    >
                      <XCircle className="h-4 w-4" />
                      Abort All Pending Messages
                    </button>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="card p-6">
                  <h3 className="text-title text-text mb-4">Queue Stats</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary">Total in Queue</span>
                      <span className="font-mono text-text">
                        {(health?.pending_count || 0) + (health?.in_progress_count || 0)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary">Failure Rate</span>
                      <span className={cn('font-mono', health?.failed_count ? 'text-error' : 'text-success')}>
                        {health?.sent_today
                          ? `${((health.failed_count / (health.sent_today + health.failed_count)) * 100).toFixed(1)}%`
                          : '0%'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary">Auto-Refresh</span>
                      <span className={cn('text-body-sm', autoRefresh ? 'text-success' : 'text-text-muted')}>
                        {autoRefresh ? 'Every 30s' : 'Disabled'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'pending' && (
              <div className="card overflow-hidden">
                {pendingMessages.length === 0 ? (
                  <div className="p-8 text-center">
                    <CheckCircle2 className="h-12 w-12 text-success mx-auto mb-4 opacity-50" />
                    <p className="text-body text-text-secondary">No pending messages in queue</p>
                  </div>
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Participant</th>
                        <th>Node</th>
                        <th>Scheduled</th>
                        <th>Attempts</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingMessages.map((msg) => {
                        const scheduledDate = new Date(msg.scheduled_at);
                        const isOverdue = scheduledDate < new Date();
                        return (
                          <tr key={msg.id}>
                            <td className="font-mono text-text-muted">#{msg.id}</td>
                            <td>
                              <Link
                                href={`/admin/projects/${projectId}/participants/${msg.participant_id}`}
                                className="text-accent hover:underline"
                              >
                                Participant #{msg.participant_id}
                              </Link>
                            </td>
                            <td className="text-text-secondary">Node #{msg.node_id}</td>
                            <td className={cn(isOverdue && 'text-warning')}>
                              <div className="flex items-center gap-1.5">
                                {isOverdue && <AlertCircle className="h-3.5 w-3.5" />}
                                {scheduledDate.toLocaleString()}
                              </div>
                            </td>
                            <td className="text-text-muted">{msg.attempt_count}</td>
                            <td>
                              <span className="badge badge-warning">{msg.status}</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {activeTab === 'failed' && (
              <div className="card overflow-hidden">
                {failedMessages.length === 0 ? (
                  <div className="p-8 text-center">
                    <CheckCircle2 className="h-12 w-12 text-success mx-auto mb-4 opacity-50" />
                    <p className="text-body text-text-secondary">No failed messages</p>
                  </div>
                ) : (
                  <>
                    <div className="px-4 py-3 bg-surface border-b border-border flex items-center justify-between">
                      <span className="text-body-sm text-text-muted">
                        {failedMessages.length} failed messages
                      </span>
                      <button
                        onClick={handleRequeue}
                        className="btn-primary text-body-sm py-1.5"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        Requeue All
                      </button>
                    </div>
                    <table className="table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Participant</th>
                          <th>Node</th>
                          <th>Attempts</th>
                          <th>Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {failedMessages.map((msg) => (
                          <tr key={msg.id}>
                            <td className="font-mono text-text-muted">#{msg.id}</td>
                            <td>
                              <Link
                                href={`/admin/projects/${projectId}/participants/${msg.participant_id}`}
                                className="text-accent hover:underline"
                              >
                                Participant #{msg.participant_id}
                              </Link>
                            </td>
                            <td className="text-text-secondary">Node #{msg.node_id}</td>
                            <td className="text-text-muted">{msg.attempt_count}</td>
                            <td>
                              <p className="text-error text-body-sm max-w-xs truncate" title={msg.error_message || ''}>
                                {msg.error_message || 'Unknown error'}
                              </p>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
