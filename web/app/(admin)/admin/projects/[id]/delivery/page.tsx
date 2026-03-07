"use client";

import { useEffect, useState, FormEvent } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout";
import {
  delivery,
  QueueStats,
  MessageSummary,
  ChannelStatus,
  ApiError,
} from "@/lib/api";
import { useToastStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  Send,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Wifi,
  WifiOff,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

type StatusFilter = "" | "PENDING" | "SENT" | "FAILED" | "IN_PROGRESS" | "SKIPPED" | "ABORTED";

export default function DeliveryPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [stats, setStats] = useState<QueueStats | null>(null);
  const [messages, setMessages] = useState<MessageSummary[]>([]);
  const [totalMessages, setTotalMessages] = useState(0);
  const [channelStatus, setChannelStatus] = useState<ChannelStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [page, setPage] = useState(1);
  const limit = 25;

  // Test send form
  const [showTestSend, setShowTestSend] = useState(false);
  const [testParticipantId, setTestParticipantId] = useState("");
  const [testMessage, setTestMessage] = useState("");
  const [testChannel, setTestChannel] = useState("");
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    loadData();
  }, [projectId]);

  useEffect(() => {
    loadMessages();
  }, [projectId, statusFilter, page]);

  async function loadData() {
    try {
      const [statsData, channelData] = await Promise.all([
        delivery.getStats(projectId),
        delivery.channelStatus(),
      ]);
      setStats(statsData);
      setChannelStatus(channelData);
    } catch {
      addToast("error", "Failed to load delivery data");
    } finally {
      setLoading(false);
    }
  }

  async function loadMessages() {
    try {
      const data = await delivery.listMessages(projectId, {
        status: statusFilter || undefined,
        page,
        limit,
      });
      setMessages(data.messages);
      setTotalMessages(data.total);
    } catch {
      // Stats may load fine, messages may fail - don't block the page
    }
  }

  async function handleRetryFailed() {
    try {
      const result = await delivery.retryFailed(projectId);
      addToast("success", `${result.retried_count} messages queued for retry`);
      loadData();
      loadMessages();
    } catch {
      addToast("error", "Failed to retry messages");
    }
  }

  async function handleTestSend(e: FormEvent) {
    e.preventDefault();
    setIsSending(true);

    try {
      const result = await delivery.testSend({
        participant_id: Number(testParticipantId),
        message_text: testMessage,
        channel_override: testChannel || undefined,
      });

      if (result.success) {
        addToast("success", `Test message sent via ${result.channel}`);
        setShowTestSend(false);
        setTestParticipantId("");
        setTestMessage("");
        setTestChannel("");
        loadData();
        loadMessages();
      } else {
        addToast("error", result.error || "Send failed");
      }
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || "Failed to send"
          : "Failed to send";
      addToast("error", message);
    } finally {
      setIsSending(false);
    }
  }

  const totalPages = Math.ceil(totalMessages / limit);

  function statusIcon(status: string) {
    switch (status) {
      case "SENT":
        return <CheckCircle className="h-4 w-4 text-success" />;
      case "FAILED":
        return <XCircle className="h-4 w-4 text-error" />;
      case "PENDING":
        return <Clock className="h-4 w-4 text-warning" />;
      case "IN_PROGRESS":
        return <RefreshCw className="h-4 w-4 text-accent animate-spin" />;
      case "SKIPPED":
        return <AlertTriangle className="h-4 w-4 text-text-muted" />;
      case "ABORTED":
        return <XCircle className="h-4 w-4 text-text-muted" />;
      default:
        return <MessageSquare className="h-4 w-4 text-text-muted" />;
    }
  }

  function statusBadgeClass(status: string) {
    switch (status) {
      case "SENT":
        return "badge badge-success";
      case "FAILED":
        return "badge badge-error";
      case "PENDING":
        return "badge badge-warning";
      case "IN_PROGRESS":
        return "badge badge-info";
      default:
        return "badge badge-default";
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Message Delivery" />
        <div className="p-6">
          <div className="card p-8 text-center">
            <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="Message Delivery"
        description={`${stats?.total || 0} total messages`}
        actions={
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowTestSend(!showTestSend)}
              className="btn-secondary"
            >
              <Send className="h-4 w-4" />
              Test Send
            </button>
            <button
              onClick={() => {
                loadData();
                loadMessages();
              }}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Channel Status */}
        {channelStatus && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card p-4">
              <div className="flex items-center gap-3">
                {channelStatus.twilio_configured ? (
                  <Wifi className="h-5 w-5 text-success" />
                ) : (
                  <WifiOff className="h-5 w-5 text-text-muted" />
                )}
                <div>
                  <p className="text-body-sm font-medium text-text">Twilio SMS</p>
                  <p className="text-caption text-text-muted">
                    {channelStatus.twilio_configured
                      ? channelStatus.twilio_phone_number || "Configured"
                      : "Not configured"}
                  </p>
                </div>
              </div>
            </div>
            <div className="card p-4">
              <div className="flex items-center gap-3">
                {channelStatus.fcm_configured ? (
                  <Wifi className="h-5 w-5 text-success" />
                ) : (
                  <WifiOff className="h-5 w-5 text-text-muted" />
                )}
                <div>
                  <p className="text-body-sm font-medium text-text">FCM Push</p>
                  <p className="text-caption text-text-muted">
                    {channelStatus.fcm_configured
                      ? "Configured"
                      : "Not configured"}
                  </p>
                </div>
              </div>
            </div>
            <div className="card p-4">
              <div className="flex items-center gap-3">
                {channelStatus.simulation_mode ? (
                  <AlertTriangle className="h-5 w-5 text-warning" />
                ) : (
                  <CheckCircle className="h-5 w-5 text-success" />
                )}
                <div>
                  <p className="text-body-sm font-medium text-text">Mode</p>
                  <p className="text-caption text-text-muted">
                    {channelStatus.simulation_mode ? "Simulation" : "Live"}
                  </p>
                </div>
              </div>
            </div>
            <div className="card p-4">
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5 text-accent" />
                <div>
                  <p className="text-body-sm font-medium text-text">Total</p>
                  <p className="text-caption text-text-muted">
                    {stats?.total || 0} messages
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Queue Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {([
              { label: "Pending", value: stats.pending, color: "text-warning" },
              { label: "In Progress", value: stats.in_progress, color: "text-accent" },
              { label: "Sent", value: stats.sent, color: "text-success" },
              { label: "Failed", value: stats.failed, color: "text-error" },
              { label: "Skipped", value: stats.skipped, color: "text-text-muted" },
              { label: "Aborted", value: stats.aborted, color: "text-text-muted" },
            ] as const).map((stat) => (
              <button
                key={stat.label}
                onClick={() => {
                  const f = stat.label.toUpperCase().replace(" ", "_") as StatusFilter;
                  setStatusFilter(statusFilter === f ? "" : f);
                  setPage(1);
                }}
                className={cn(
                  "card p-4 text-center transition-all hover:shadow-md cursor-pointer",
                  statusFilter === stat.label.toUpperCase().replace(" ", "_") &&
                    "ring-2 ring-accent",
                )}
              >
                <p className={cn("text-2xl font-bold", stat.color)}>
                  {stat.value}
                </p>
                <p className="text-caption text-text-muted">{stat.label}</p>
              </button>
            ))}
          </div>
        )}

        {/* Retry Failed Button */}
        {stats && stats.failed > 0 && (
          <div className="flex items-center gap-3">
            <button onClick={handleRetryFailed} className="btn-secondary">
              <RefreshCw className="h-4 w-4" />
              Retry {stats.failed} failed messages
            </button>
          </div>
        )}

        {/* Test Send Form */}
        {showTestSend && (
          <div className="card p-6">
            <h3 className="text-title text-text mb-4">Send Test Message</h3>
            <form onSubmit={handleTestSend} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="label">
                    Participant ID <span className="text-error">*</span>
                  </label>
                  <input
                    type="number"
                    value={testParticipantId}
                    onChange={(e) => setTestParticipantId(e.target.value)}
                    className="input"
                    required
                    min={1}
                    placeholder="e.g., 42"
                  />
                </div>
                <div>
                  <label className="label">Channel Override</label>
                  <select
                    value={testChannel}
                    onChange={(e) => setTestChannel(e.target.value)}
                    className="input"
                  >
                    <option value="">Auto (participant default)</option>
                    <option value="TWILIO">Twilio SMS</option>
                    <option value="MOBILE_APP">FCM Push</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="label">
                  Message Text <span className="text-error">*</span>
                </label>
                <textarea
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  className="input min-h-[80px] resize-y"
                  required
                  placeholder="Enter test message..."
                  rows={3}
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={isSending}
                  className="btn-primary"
                >
                  {isSending ? "Sending..." : "Send Test Message"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowTestSend(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Message List */}
        <div className="card overflow-hidden">
          <div className="px-4 py-3 bg-surface border-b border-border flex items-center justify-between">
            <h3 className="text-title text-text">
              Messages
              {statusFilter && (
                <span className="ml-2 text-body-sm text-text-muted font-normal">
                  filtered by {statusFilter}
                </span>
              )}
            </h3>
            {statusFilter && (
              <button
                onClick={() => {
                  setStatusFilter("");
                  setPage(1);
                }}
                className="btn-ghost text-body-sm"
              >
                Clear filter
              </button>
            )}
          </div>

          {messages.length === 0 ? (
            <div className="p-8 text-center text-text-muted">
              <MessageSquare className="h-8 w-8 mx-auto mb-3 opacity-50" />
              <p>No messages found</p>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Participant</th>
                  <th>Channel</th>
                  <th>Message</th>
                  <th>Scheduled</th>
                  <th>Sent</th>
                  <th>Attempts</th>
                </tr>
              </thead>
              <tbody>
                {messages.map((msg) => (
                  <tr key={msg.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        {statusIcon(msg.status)}
                        <span className={statusBadgeClass(msg.status)}>
                          {msg.status}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div>
                        <p className="text-body-sm font-mono text-text">
                          #{msg.participant_id}
                        </p>
                        {msg.participant_uuid && (
                          <p className="text-caption text-text-muted truncate max-w-[120px]">
                            {msg.participant_uuid}
                          </p>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-default">
                        {msg.channel_type}
                      </span>
                    </td>
                    <td className="max-w-[200px]">
                      <p className="text-body-sm text-text truncate">
                        {msg.message_body || (
                          <span className="text-text-muted italic">
                            Template #{msg.template_id}
                          </span>
                        )}
                      </p>
                      {msg.last_error_message && (
                        <p className="text-caption text-error truncate">
                          {msg.last_error_message}
                        </p>
                      )}
                    </td>
                    <td className="text-body-sm text-text-muted whitespace-nowrap">
                      {new Date(msg.send_at).toLocaleString()}
                    </td>
                    <td className="text-body-sm text-text-muted whitespace-nowrap">
                      {msg.sent_at
                        ? new Date(msg.sent_at).toLocaleString()
                        : "-"}
                    </td>
                    <td className="text-body-sm text-text-muted text-center">
                      {msg.attempt_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-4 py-3 border-t border-border flex items-center justify-between">
              <p className="text-body-sm text-text-muted">
                Page {page} of {totalPages} ({totalMessages} total)
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page <= 1}
                  className="btn-ghost p-2 disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page >= totalPages}
                  className="btn-ghost p-2 disabled:opacity-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
