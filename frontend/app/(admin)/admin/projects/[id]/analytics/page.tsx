'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { analytics, OverviewStats, DeliveryStats, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  RefreshCw,
  Users,
  UserCheck,
  UserX,
  Trophy,
  MessageSquare,
  Clock,
  AlertCircle,
  CheckCircle2,
  Send,
  XCircle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Calendar,
  Loader2,
} from 'lucide-react';

export default function AnalyticsPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [delivery, setDelivery] = useState<DeliveryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      const [overviewData, deliveryData] = await Promise.all([
        analytics.overview(projectId),
        analytics.delivery(projectId),
      ]);
      setOverview(overviewData);
      setDelivery(deliveryData);
    } catch (err) {
      if (!silent) {
        addToast('error', 'Failed to load analytics');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [projectId, addToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const participantCompletionRate = overview
    ? overview.total_participants > 0
      ? ((overview.completed_participants / overview.total_participants) * 100).toFixed(1)
      : '0'
    : '0';

  const participantActiveRate = overview
    ? overview.total_participants > 0
      ? ((overview.active_participants / overview.total_participants) * 100).toFixed(1)
      : '0'
    : '0';

  return (
    <>
      <Header
        title="Analytics"
        description="Project performance metrics and insights"
        actions={
          <div className="flex items-center gap-3">
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
            <p className="mt-2 text-text-muted">Loading analytics...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Participant Overview */}
            <div>
              <h2 className="text-title text-text mb-4 flex items-center gap-2">
                <Users className="h-5 w-5 text-accent" />
                Participant Overview
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Participants */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Total Participants</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {overview?.total_participants || 0}
                      </p>
                    </div>
                    <div className="p-2.5 bg-accent/10 rounded-lg">
                      <Users className="h-6 w-6 text-accent" />
                    </div>
                  </div>
                </div>

                {/* Active Participants */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Active</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {overview?.active_participants || 0}
                      </p>
                      <p className="text-caption text-success mt-1">
                        {participantActiveRate}% of total
                      </p>
                    </div>
                    <div className="p-2.5 bg-success/10 rounded-lg">
                      <UserCheck className="h-6 w-6 text-success" />
                    </div>
                  </div>
                </div>

                {/* Completed Participants */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Completed</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {overview?.completed_participants || 0}
                      </p>
                      <p className="text-caption text-accent mt-1">
                        {participantCompletionRate}% completion
                      </p>
                    </div>
                    <div className="p-2.5 bg-accent/10 rounded-lg">
                      <Trophy className="h-6 w-6 text-accent" />
                    </div>
                  </div>
                </div>

                {/* Dropped/Inactive */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Dropped/Inactive</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {(overview?.total_participants || 0) -
                          (overview?.active_participants || 0) -
                          (overview?.completed_participants || 0)}
                      </p>
                    </div>
                    <div className="p-2.5 bg-error/10 rounded-lg">
                      <UserX className="h-6 w-6 text-error" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Message Delivery */}
            <div>
              <h2 className="text-title text-text mb-4 flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-accent" />
                Message Delivery
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Sent */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Total Sent</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {delivery?.total_sent || 0}
                      </p>
                    </div>
                    <div className="p-2.5 bg-success/10 rounded-lg">
                      <Send className="h-6 w-6 text-success" />
                    </div>
                  </div>
                </div>

                {/* Pending */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Pending</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {delivery?.total_pending || 0}
                      </p>
                    </div>
                    <div className="p-2.5 bg-warning/10 rounded-lg">
                      <Clock className="h-6 w-6 text-warning" />
                    </div>
                  </div>
                </div>

                {/* Failed */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Failed</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {delivery?.total_failed || 0}
                      </p>
                    </div>
                    <div className="p-2.5 bg-error/10 rounded-lg">
                      <AlertCircle className="h-6 w-6 text-error" />
                    </div>
                  </div>
                </div>

                {/* Aborted */}
                <div className="card p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-caption text-text-muted">Aborted</p>
                      <p className="text-2xl font-bold text-text mt-1">
                        {delivery?.total_aborted || 0}
                      </p>
                    </div>
                    <div className="p-2.5 bg-surface rounded-lg">
                      <XCircle className="h-6 w-6 text-text-muted" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Delivery Performance */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Delivery Rate Card */}
              <div className="card p-6">
                <h3 className="text-title text-text mb-4 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-success" />
                  Delivery Rate
                </h3>
                <div className="flex items-center gap-8">
                  {/* Big percentage */}
                  <div className="flex-shrink-0">
                    <div
                      className={cn(
                        'text-5xl font-bold',
                        (overview?.delivery_rate || 0) >= 95
                          ? 'text-success'
                          : (overview?.delivery_rate || 0) >= 80
                          ? 'text-warning'
                          : 'text-error'
                      )}
                    >
                      {overview?.delivery_rate || 0}%
                    </div>
                    <p className="text-caption text-text-muted mt-1">
                      Success rate
                    </p>
                  </div>

                  {/* Progress bar visual */}
                  <div className="flex-1">
                    <div className="h-4 bg-surface rounded-full overflow-hidden">
                      <div
                        className={cn(
                          'h-full transition-all duration-500',
                          (overview?.delivery_rate || 0) >= 95
                            ? 'bg-success'
                            : (overview?.delivery_rate || 0) >= 80
                            ? 'bg-warning'
                            : 'bg-error'
                        )}
                        style={{ width: `${overview?.delivery_rate || 0}%` }}
                      />
                    </div>
                    <div className="flex justify-between mt-2 text-caption text-text-muted">
                      <span>0%</span>
                      <span>Target: 95%</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>

                {/* Status indicator */}
                <div
                  className={cn(
                    'mt-4 p-3 rounded-lg flex items-center gap-2',
                    (overview?.delivery_rate || 0) >= 95
                      ? 'bg-success/10 text-success'
                      : (overview?.delivery_rate || 0) >= 80
                      ? 'bg-warning/10 text-warning'
                      : 'bg-error/10 text-error'
                  )}
                >
                  {(overview?.delivery_rate || 0) >= 95 ? (
                    <>
                      <CheckCircle2 className="h-4 w-4" />
                      <span className="text-body-sm">Excellent delivery performance</span>
                    </>
                  ) : (overview?.delivery_rate || 0) >= 80 ? (
                    <>
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-body-sm">Delivery rate below target</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4" />
                      <span className="text-body-sm">Critical: Low delivery rate</span>
                    </>
                  )}
                </div>
              </div>

              {/* Recent Activity */}
              <div className="card p-6">
                <h3 className="text-title text-text mb-4 flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-accent" />
                  Recent Activity
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-surface rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-success/10 rounded">
                        <Send className="h-4 w-4 text-success" />
                      </div>
                      <div>
                        <p className="text-body font-medium text-text">Sent Today</p>
                        <p className="text-caption text-text-muted">Last 24 hours</p>
                      </div>
                    </div>
                    <span className="text-xl font-bold text-text">
                      {delivery?.sent_today || 0}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-surface rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-accent/10 rounded">
                        <BarChart3 className="h-4 w-4 text-accent" />
                      </div>
                      <div>
                        <p className="text-body font-medium text-text">Sent This Week</p>
                        <p className="text-caption text-text-muted">Last 7 days</p>
                      </div>
                    </div>
                    <span className="text-xl font-bold text-text">
                      {delivery?.sent_this_week || 0}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-surface rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-warning/10 rounded">
                        <Clock className="h-4 w-4 text-warning" />
                      </div>
                      <div>
                        <p className="text-body font-medium text-text">Avg per Day</p>
                        <p className="text-caption text-text-muted">This week</p>
                      </div>
                    </div>
                    <span className="text-xl font-bold text-text">
                      {delivery?.sent_this_week
                        ? Math.round(delivery.sent_this_week / 7)
                        : 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card p-5 border-l-4 border-l-success">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-8 w-8 text-success" />
                  <div>
                    <p className="text-caption text-text-muted">Messages Delivered</p>
                    <p className="text-title text-text">
                      {overview?.total_messages_sent || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-5 border-l-4 border-l-warning">
                <div className="flex items-center gap-3">
                  <Clock className="h-8 w-8 text-warning" />
                  <div>
                    <p className="text-caption text-text-muted">Messages Pending</p>
                    <p className="text-title text-text">
                      {overview?.messages_pending || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-5 border-l-4 border-l-error">
                <div className="flex items-center gap-3">
                  <AlertCircle className="h-8 w-8 text-error" />
                  <div>
                    <p className="text-caption text-text-muted">Messages Failed</p>
                    <p className="text-title text-text">
                      {overview?.messages_failed || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
