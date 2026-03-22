'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import {
  participants,
  scheduler,
  Participant,
  ParticipantVariable,
  ParticipantMessage,
  ApiError,
} from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { formatDateTime, getStatusVariant, cn } from '@/lib/utils';
import {
  ArrowLeft,
  User,
  Phone,
  Globe,
  Calendar,
  Clock,
  MessageSquare,
  Variable,
  Edit2,
  Save,
  X,
  CheckCircle2,
  AlertCircle,
  Send,
  XCircle,
  Loader2,
  ChevronRight,
  RefreshCw,
  Trash2,
} from 'lucide-react';

type TabType = 'overview' | 'variables' | 'messages';

export default function ParticipantDetailPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const participantId = Number(params.participantId);
  const { addToast } = useToastStore();

  const [participant, setParticipant] = useState<Participant | null>(null);
  const [variables, setVariables] = useState<ParticipantVariable[]>([]);
  const [messages, setMessages] = useState<ParticipantMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [editingVariable, setEditingVariable] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [participantData, variablesData, messagesData] = await Promise.all([
        participants.get(participantId),
        participants.getVariables(participantId),
        participants.getMessages(participantId, 100),
      ]);
      setParticipant(participantData);
      setVariables(variablesData);
      setMessages(messagesData);
    } catch (err) {
      addToast('error', 'Failed to load participant data');
    } finally {
      setLoading(false);
    }
  }, [participantId, addToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleSaveVariable(variableId: number) {
    setSaving(true);
    try {
      await participants.updateVariable(participantId, variableId, editValue || null);
      addToast('success', 'Variable updated');
      setEditingVariable(null);
      // Reload variables
      const variablesData = await participants.getVariables(participantId);
      setVariables(variablesData);
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to update variable');
    } finally {
      setSaving(false);
    }
  }

  async function handleAbortMessages() {
    if (!confirm('Abort all pending messages for this participant?')) return;

    try {
      const result = await scheduler.abortParticipant(participantId);
      addToast('success', result.message);
      // Reload messages
      const messagesData = await participants.getMessages(participantId, 100);
      setMessages(messagesData);
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to abort messages');
    }
  }

  function startEditVariable(variable: ParticipantVariable) {
    setEditingVariable(variable.variable_id);
    setEditValue(variable.value || '');
  }

  function cancelEdit() {
    setEditingVariable(null);
    setEditValue('');
  }

  const getMessageStatusIcon = (status: string) => {
    switch (status) {
      case 'SENT':
        return <CheckCircle2 className="h-4 w-4 text-success" />;
      case 'PENDING':
        return <Clock className="h-4 w-4 text-warning" />;
      case 'FAILED':
        return <AlertCircle className="h-4 w-4 text-error" />;
      case 'ABORTED':
        return <XCircle className="h-4 w-4 text-text-muted" />;
      default:
        return <MessageSquare className="h-4 w-4 text-text-muted" />;
    }
  };

  if (loading) {
    return (
      <>
        <Header title="Loading..." />
        <div className="p-6">
          <div className="card p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-accent" />
          </div>
        </div>
      </>
    );
  }

  if (!participant) {
    return (
      <>
        <Header title="Participant Not Found" />
        <div className="p-6">
          <div className="card p-8 text-center">
            <p className="text-body text-text-secondary mb-4">
              The participant you're looking for doesn't exist.
            </p>
            <Link
              href={`/admin/projects/${projectId}/participants`}
              className="btn-primary"
            >
              Back to Participants
            </Link>
          </div>
        </div>
      </>
    );
  }

  const pendingMessagesCount = messages.filter((m) => m.status === 'PENDING').length;

  return (
    <>
      <Header
        title={`Participant ${participant.external_id || participant.uu_id || `#${participant.id}`}`}
        description={participant.uu_id || undefined}
        actions={
          <div className="flex items-center gap-3">
            <button onClick={() => loadData()} className="btn-secondary">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <Link
              href={`/admin/projects/${projectId}/participants`}
              className="btn-secondary"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Status Banner */}
        <div
          className={cn(
            'card p-4 flex items-center justify-between',
            participant.status === 'ACTIVE' && 'border-l-4 border-l-success',
            participant.status === 'COMPLETED' && 'border-l-4 border-l-accent',
            participant.status === 'SUSPENDED' && 'border-l-4 border-l-warning',
            participant.status === 'INACTIVE' && 'border-l-4 border-l-error',
            participant.status === 'BLOCKED_SYSTEM' && 'border-l-4 border-l-error'
          )}
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-surface rounded-full">
              <User className="h-6 w-6 text-text-muted" />
            </div>
            <div>
              <div className="flex items-center gap-2">
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
                {participant.is_test_participant && (
                  <span className="badge badge-default">Test</span>
                )}
              </div>
              <p className="text-body-sm text-text-muted mt-1">
                {participant.channel_type} • Language ID: {participant.language_id}
              </p>
            </div>
          </div>
          {pendingMessagesCount > 0 && (
            <button onClick={handleAbortMessages} className="btn-ghost text-error">
              <Trash2 className="h-4 w-4" />
              Abort {pendingMessagesCount} Pending
            </button>
          )}
        </div>

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
            <User className="h-4 w-4 inline mr-1.5" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('variables')}
            className={cn(
              'px-4 py-2 text-body-sm font-medium border-b-2 transition-colors',
              activeTab === 'variables'
                ? 'border-accent text-accent'
                : 'border-transparent text-text-muted hover:text-text'
            )}
          >
            <Variable className="h-4 w-4 inline mr-1.5" />
            Variables ({variables.length})
          </button>
          <button
            onClick={() => setActiveTab('messages')}
            className={cn(
              'px-4 py-2 text-body-sm font-medium border-b-2 transition-colors',
              activeTab === 'messages'
                ? 'border-accent text-accent'
                : 'border-transparent text-text-muted hover:text-text'
            )}
          >
            <MessageSquare className="h-4 w-4 inline mr-1.5" />
            Messages ({messages.length})
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Info Card */}
            <div className="card p-6">
              <h3 className="text-title text-text mb-4">Participant Info</h3>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-surface rounded">
                    <User className="h-4 w-4 text-text-muted" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">ID</p>
                    <p className="text-body font-mono text-text">#{participant.id}</p>
                  </div>
                </div>

                {participant.external_id && (
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-surface rounded">
                      <Globe className="h-4 w-4 text-text-muted" />
                    </div>
                    <div>
                      <p className="text-caption text-text-muted">External ID</p>
                      <p className="text-body text-text">{participant.external_id}</p>
                    </div>
                  </div>
                )}

                {participant.uu_id && (
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-surface rounded">
                      <Globe className="h-4 w-4 text-text-muted" />
                    </div>
                    <div>
                      <p className="text-caption text-text-muted">UUID</p>
                      <p className="text-body font-mono text-text text-sm">{participant.uu_id}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <div className="p-2 bg-surface rounded">
                    <Phone className="h-4 w-4 text-text-muted" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Channel</p>
                    <p className="text-body text-text">{participant.channel_type}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Timeline Card */}
            <div className="card p-6">
              <h3 className="text-title text-text mb-4">Timeline</h3>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-success/10 rounded">
                    <Calendar className="h-4 w-4 text-success" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Enrolled</p>
                    <p className="text-body text-text">
                      {participant.enrolled_at
                        ? formatDateTime(participant.enrolled_at)
                        : 'Not set'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="p-2 bg-surface rounded">
                    <Calendar className="h-4 w-4 text-text-muted" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Created</p>
                    <p className="text-body text-text">
                      {formatDateTime(participant.created_at)}
                    </p>
                  </div>
                </div>

                {participant.completed_at && (
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-accent/10 rounded">
                      <CheckCircle2 className="h-4 w-4 text-accent" />
                    </div>
                    <div>
                      <p className="text-caption text-text-muted">Completed</p>
                      <p className="text-body text-text">
                        {formatDateTime(participant.completed_at)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="card p-6 lg:col-span-2">
              <h3 className="text-title text-text mb-4">Message Stats</h3>
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center p-4 bg-surface rounded-lg">
                  <p className="text-2xl font-bold text-success">
                    {messages.filter((m) => m.status === 'SENT').length}
                  </p>
                  <p className="text-caption text-text-muted">Sent</p>
                </div>
                <div className="text-center p-4 bg-surface rounded-lg">
                  <p className="text-2xl font-bold text-warning">
                    {messages.filter((m) => m.status === 'PENDING').length}
                  </p>
                  <p className="text-caption text-text-muted">Pending</p>
                </div>
                <div className="text-center p-4 bg-surface rounded-lg">
                  <p className="text-2xl font-bold text-error">
                    {messages.filter((m) => m.status === 'FAILED').length}
                  </p>
                  <p className="text-caption text-text-muted">Failed</p>
                </div>
                <div className="text-center p-4 bg-surface rounded-lg">
                  <p className="text-2xl font-bold text-text-muted">
                    {messages.filter((m) => m.status === 'ABORTED').length}
                  </p>
                  <p className="text-caption text-text-muted">Aborted</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'variables' && (
          <div className="card overflow-hidden">
            {variables.length === 0 ? (
              <div className="p-8 text-center">
                <Variable className="h-12 w-12 text-text-muted mx-auto mb-4" />
                <p className="text-body text-text-secondary">
                  No variables defined for this project
                </p>
              </div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th>Type</th>
                    <th>Value</th>
                    <th className="w-24"></th>
                  </tr>
                </thead>
                <tbody>
                  {variables.map((variable) => (
                    <tr key={variable.variable_id}>
                      <td>
                        <div>
                          <p className="font-mono font-medium text-text">
                            {`{{${variable.variable_name}}}`}
                          </p>
                          {variable.variable_display_name && (
                            <p className="text-caption text-text-muted">
                              {variable.variable_display_name}
                            </p>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="badge badge-default">{variable.variable_type}</span>
                      </td>
                      <td>
                        {editingVariable === variable.variable_id ? (
                          <input
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="input font-mono w-full max-w-xs"
                            autoFocus
                          />
                        ) : (
                          <span className="font-mono text-text-secondary">
                            {variable.value || <span className="text-text-muted italic">empty</span>}
                          </span>
                        )}
                      </td>
                      <td>
                        {editingVariable === variable.variable_id ? (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleSaveVariable(variable.variable_id)}
                              disabled={saving}
                              className="btn-primary p-1.5"
                            >
                              {saving ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Save className="h-4 w-4" />
                              )}
                            </button>
                            <button onClick={cancelEdit} className="btn-ghost p-1.5">
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => startEditVariable(variable)}
                            className="btn-ghost p-1.5"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'messages' && (
          <div className="card overflow-hidden">
            {messages.length === 0 ? (
              <div className="p-8 text-center">
                <MessageSquare className="h-12 w-12 text-text-muted mx-auto mb-4" />
                <p className="text-body text-text-secondary">No messages yet</p>
              </div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Direction</th>
                    <th>Message</th>
                    <th>Scheduled</th>
                    <th>Sent</th>
                  </tr>
                </thead>
                <tbody>
                  {messages.map((message) => (
                    <tr key={message.id}>
                      <td>
                        <div className="flex items-center gap-2">
                          {getMessageStatusIcon(message.status)}
                          <span
                            className={cn('badge', {
                              'badge-success': message.status === 'SENT',
                              'badge-warning': message.status === 'PENDING',
                              'badge-error': message.status === 'FAILED',
                              'badge-default':
                                message.status === 'ABORTED' ||
                                message.status === 'SKIPPED',
                            })}
                          >
                            {message.status}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-1.5">
                          {message.direction === 'OUTGOING' ? (
                            <>
                              <Send className="h-3.5 w-3.5 text-accent" />
                              <span className="text-text-secondary">Out</span>
                            </>
                          ) : (
                            <>
                              <ChevronRight className="h-3.5 w-3.5 text-success" />
                              <span className="text-text-secondary">In</span>
                            </>
                          )}
                        </div>
                      </td>
                      <td>
                        {message.message_body ? (
                          <p
                            className="text-body-sm text-text max-w-xs truncate"
                            title={message.message_body}
                          >
                            {message.message_body}
                          </p>
                        ) : (
                          <span className="text-text-muted italic">
                            {message.template_id ? `Template #${message.template_id}` : '-'}
                          </span>
                        )}
                      </td>
                      <td className="text-text-secondary text-body-sm">
                        {formatDateTime(message.scheduled_at)}
                      </td>
                      <td className="text-text-secondary text-body-sm">
                        {message.sent_at ? formatDateTime(message.sent_at) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </>
  );
}
