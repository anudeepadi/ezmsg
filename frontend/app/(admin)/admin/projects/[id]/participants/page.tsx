'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { participants, Participant, ParticipantListResponse, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { formatDateTime, getStatusVariant, cn } from '@/lib/utils';
import {
  ArrowLeft,
  Plus,
  Search,
  ChevronLeft,
  ChevronRight,
  User,
} from 'lucide-react';

const statusOptions = ['', 'ACTIVE', 'PAUSED', 'COMPLETED', 'WITHDRAWN'];

export default function ParticipantsPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [data, setData] = useState<ParticipantListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadParticipants();
  }, [projectId, page, statusFilter]);

  async function loadParticipants() {
    setLoading(true);
    try {
      const result = await participants.list(projectId, page, 25, statusFilter || undefined);
      setData(result);
    } catch (err) {
      addToast('error', 'Failed to load participants');
    } finally {
      setLoading(false);
    }
  }

  const totalPages = data ? Math.ceil(data.total / data.size) : 0;

  const filteredItems = data?.items.filter(
    (p) =>
      !search ||
      p.external_id?.toLowerCase().includes(search.toLowerCase()) ||
      p.uu_id?.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <>
      <Header
        title="Participants"
        description={`${data?.total || 0} participants enrolled`}
        actions={
          <div className="flex items-center gap-3">
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <Link
              href={`/admin/projects/${projectId}/participants/new`}
              className="btn-primary"
            >
              <Plus className="h-4 w-4" />
              Add Participant
            </Link>
          </div>
        }
      />

      <div className="p-6">
        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search by ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="input w-40"
          >
            <option value="">All Status</option>
            {statusOptions.slice(1).map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {/* Table */}
        <div className="card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-8 text-center">
              <User className="h-12 w-12 text-text-muted mx-auto mb-4" />
              <p className="text-body text-text-secondary mb-4">
                {search || statusFilter
                  ? 'No participants match your filters'
                  : 'No participants enrolled yet'}
              </p>
              {!search && !statusFilter && (
                <Link
                  href={`/admin/projects/${projectId}/participants/new`}
                  className="btn-primary"
                >
                  <Plus className="h-4 w-4" />
                  Add first participant
                </Link>
              )}
            </div>
          ) : (
            <>
              <table className="table">
                <thead>
                  <tr>
                    <th>Participant</th>
                    <th>Status</th>
                    <th>Channel</th>
                    <th>Test</th>
                    <th>Enrolled</th>
                    <th>Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((participant) => (
                    <tr key={participant.id}>
                      <td>
                        <Link
                          href={`/admin/projects/${projectId}/participants/${participant.id}`}
                          className="font-medium text-text hover:text-accent transition-colors"
                        >
                          {participant.external_id || participant.uu_id || `#${participant.id}`}
                        </Link>
                        {participant.uu_id && participant.external_id && (
                          <p className="text-caption text-text-muted font-mono">
                            {participant.uu_id.slice(0, 8)}...
                          </p>
                        )}
                      </td>
                      <td>
                        <span
                          className={cn('badge', {
                            'badge-success': getStatusVariant(participant.status) === 'success',
                            'badge-warning': getStatusVariant(participant.status) === 'warning',
                            'badge-error': getStatusVariant(participant.status) === 'error',
                            'badge-default': getStatusVariant(participant.status) === 'default',
                          })}
                        >
                          {participant.status}
                        </span>
                      </td>
                      <td className="text-text-secondary">
                        {participant.channel_type}
                      </td>
                      <td>
                        {participant.is_test_participant && (
                          <span className="badge badge-default">Test</span>
                        )}
                      </td>
                      <td className="text-text-secondary">
                        {participant.enrolled_at
                          ? formatDateTime(participant.enrolled_at)
                          : '-'}
                      </td>
                      <td className="text-text-secondary">
                        {participant.completed_at
                          ? formatDateTime(participant.completed_at)
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-border">
                  <p className="text-body-sm text-text-secondary">
                    Showing {(page - 1) * (data?.size || 25) + 1} to{' '}
                    {Math.min(page * (data?.size || 25), data?.total || 0)} of{' '}
                    {data?.total} results
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page === 1}
                      className="btn-ghost p-2"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    <span className="text-body-sm text-text">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(Math.min(totalPages, page + 1))}
                      disabled={page === totalPages}
                      className="btn-ghost p-2"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
