'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/layout';
import {
  scheduler,
  QueueHealth,
  ScheduledMessage,
  ApiError,
} from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { formatDateTime, cn } from '@/lib/utils';
import {
  RefreshCw,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RotateCcw,
} from 'lucide-react';

export default function SchedulerPage() {
  const { addToast } = useToastStore();

  const [health, setHealth] = useState<QueueHealth | null>(null);
  const [pendingMessages, setPendingMessages] = useState<ScheduledMessage[]>([]);
  const [failedMessages, setFailedMessages] = useState<ScheduledMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [requeueing, setRequeueing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [healthData, pending, failed] = await Promise.all([
        scheduler.health(),
        scheduler.pending(undefined, 50),
        scheduler.failed(undefined, 50),
      ]);
      setHealth(healthData);
      setPendingMessages(pending);
      setFailedMessages(failed);
    } catch (err) {
      addToast('error', 'Failed to load scheduler data');
    } finally {
      setLoading(false);
    }
  }

  async function handleRequeue() {
    setRequeueing(true);
    try {
      const result = await scheduler.requeue(24);
      addToast('success', result.message);
      loadData();
    } catch (err) {
      addToast('error', 'Failed to requeue messages');
    } finally {
      setRequeueing(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Scheduler" />
        <div className="p-6">
          <div className="animate-pulse space-y-6">
            <div className="grid grid-cols-5 gap-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-24 bg-surface rounded-lg" />
              ))}
            </div>
            <div className="h-64 bg-surface rounded-lg" />
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="Scheduler"
        description="Monitor message queue and delivery status"
        actions={
          <button onClick={loadData} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Health Stats */}
        {health && (
          <div className="grid grid-cols-5 gap-4">
            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-warning-light rounded-lg">
                  <Clock className="h-5 w-5 text-warning" />
                </div>
                <div>
                  <p className="text-caption text-text-muted">Pending</p>
                  <p className="text-title text-text">{health.pending_count}</p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-accent-light rounded-lg">
                  <RefreshCw className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <p className="text-caption text-text-muted">In Progress</p>
                  <p className="text-title text-text">{health.in_progress_count}</p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-success-light rounded-lg">
                  <CheckCircle className="h-5 w-5 text-success" />
                </div>
                <div>
                  <p className="text-caption text-text-muted">Sent Today</p>
                  <p className="text-title text-success">{health.sent_today}</p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div
                  className={cn('p-2.5 rounded-lg', {
                    'bg-error-light': health.failed_count > 0,
                    'bg-background': health.failed_count === 0,
                  })}
                >
                  <XCircle
                    className={cn('h-5 w-5', {
                      'text-error': health.failed_count > 0,
                      'text-text-muted': health.failed_count === 0,
                    })}
                  />
                </div>
                <div>
                  <p className="text-caption text-text-muted">Failed</p>
                  <p
                    className={cn('text-title', {
                      'text-error': health.failed_count > 0,
                      'text-text': health.failed_count === 0,
                    })}
                  >
                    {health.failed_count}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-background rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-caption text-text-muted">Oldest Pending</p>
                  <p className="text-title text-text">
                    {health.oldest_pending_minutes
                      ? `${Math.round(health.oldest_pending_minutes)}m`
                      : '-'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Failed Messages */}
        <div className="card">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h2 className="text-subtitle text-text">Failed Messages</h2>
            {failedMessages.length > 0 && (
              <button
                onClick={handleRequeue}
                disabled={requeueing}
                className="btn-secondary"
              >
                <RotateCcw className="h-4 w-4" />
                {requeueing ? 'Requeueing...' : 'Requeue All'}
              </button>
            )}
          </div>

          {failedMessages.length === 0 ? (
            <div className="p-8 text-center">
              <CheckCircle className="h-12 w-12 text-success mx-auto mb-4" />
              <p className="text-body text-text-secondary">
                No failed messages. Everything is running smoothly.
              </p>
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
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {failedMessages.map((msg) => (
                  <tr key={msg.id}>
                    <td className="font-mono text-text-muted">#{msg.id}</td>
                    <td>#{msg.participant_id}</td>
                    <td>#{msg.node_id}</td>
                    <td className="text-text-secondary">
                      {formatDateTime(msg.scheduled_at)}
                    </td>
                    <td>
                      <span className="badge badge-error">{msg.attempt_count}</span>
                    </td>
                    <td className="max-w-xs truncate text-error text-body-sm">
                      {msg.error_message || 'Unknown error'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pending Messages */}
        <div className="card">
          <div className="p-4 border-b border-border">
            <h2 className="text-subtitle text-text">Pending Messages</h2>
          </div>

          {pendingMessages.length === 0 ? (
            <div className="p-8 text-center">
              <Clock className="h-12 w-12 text-text-muted mx-auto mb-4" />
              <p className="text-body text-text-secondary">
                No messages in queue.
              </p>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Participant</th>
                  <th>Node</th>
                  <th>Scheduled For</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {pendingMessages.slice(0, 20).map((msg) => (
                  <tr key={msg.id}>
                    <td className="font-mono text-text-muted">#{msg.id}</td>
                    <td>#{msg.participant_id}</td>
                    <td>#{msg.node_id}</td>
                    <td className="text-text-secondary">
                      {formatDateTime(msg.scheduled_at)}
                    </td>
                    <td>
                      <span className="badge badge-warning">{msg.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {pendingMessages.length > 20 && (
            <div className="p-4 border-t border-border text-center">
              <p className="text-body-sm text-text-muted">
                Showing 20 of {pendingMessages.length} pending messages
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
