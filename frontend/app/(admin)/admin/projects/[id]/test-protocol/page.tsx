'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import {
  protocolTest,
  ProtocolOverview,
  ProtocolTestResult,
  FlowStep,
  ApiError,
} from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Play,
  RefreshCw,
  CheckCircle2,
  Circle,
  ArrowRight,
  MessageSquare,
  Clock,
  User,
  GitBranch,
  Loader2,
  ChevronDown,
  ChevronRight,
  Calendar,
  Zap,
  Flag,
  UserPlus,
} from 'lucide-react';

export default function TestProtocolPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [overview, setOverview] = useState<ProtocolOverview | null>(null);
  const [testResult, setTestResult] = useState<ProtocolTestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [creatingParticipant, setCreatingParticipant] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [activeStep, setActiveStep] = useState<number | null>(null);

  useEffect(() => {
    loadOverview();
  }, [projectId]);

  async function loadOverview() {
    setLoading(true);
    try {
      const data = await protocolTest.overview(projectId);
      setOverview(data);
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to load protocol overview');
    } finally {
      setLoading(false);
    }
  }

  async function runTest() {
    setRunning(true);
    setTestResult(null);
    try {
      const data = await protocolTest.run(projectId, { language_id: 1 });
      setTestResult(data);
      addToast('success', `Protocol test completed: ${data.total_nodes_in_flow} nodes in flow`);

      // Auto-expand first few steps
      setExpandedSteps(new Set([0, 1, 2]));
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to run protocol test');
    } finally {
      setRunning(false);
    }
  }

  async function createTestParticipant() {
    setCreatingParticipant(true);
    try {
      const data = await protocolTest.createTestParticipant(projectId, { language_id: 1 });
      addToast(
        'success',
        `Test participant created! First message scheduled for ${new Date(data.first_message_scheduled_at).toLocaleString()}`
      );
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to create test participant');
    } finally {
      setCreatingParticipant(false);
    }
  }

  function toggleStep(index: number) {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSteps(newExpanded);
  }

  function expandAll() {
    if (testResult) {
      setExpandedSteps(new Set(testResult.flow_steps.map((_, i) => i)));
    }
  }

  function collapseAll() {
    setExpandedSteps(new Set());
  }

  return (
    <>
      <Header
        title="Test Protocol Flow"
        description="Simulate and test the messaging protocol"
        actions={
          <div className="flex items-center gap-3">
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <button
              onClick={runTest}
              disabled={running || loading}
              className="btn-primary"
            >
              {running ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Run Test
                </>
              )}
            </button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {loading ? (
          <div className="card p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-accent" />
            <p className="mt-2 text-text-muted">Loading protocol...</p>
          </div>
        ) : overview ? (
          <>
            {/* Overview Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-accent/10 rounded-lg">
                    <GitBranch className="h-5 w-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Nodes</p>
                    <p className="text-title text-text">{overview.total_nodes}</p>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-success/10 rounded-lg">
                    <MessageSquare className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Templates</p>
                    <p className="text-title text-text">{overview.total_templates}</p>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-warning/10 rounded-lg">
                    <Zap className="h-5 w-5 text-warning" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Entry Points</p>
                    <p className="text-title text-text">{overview.entry_nodes.length}</p>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-error/10 rounded-lg">
                    <Flag className="h-5 w-5 text-error" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">End Points</p>
                    <p className="text-title text-text">{overview.terminal_nodes.length}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Entry/Terminal Nodes */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card p-4">
                <h3 className="text-body font-medium text-text mb-3 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-warning" />
                  Entry Nodes
                </h3>
                <div className="space-y-2">
                  {overview.entry_nodes.map((node) => (
                    <div
                      key={node.id}
                      className="p-2 bg-warning/10 rounded font-mono text-body-sm"
                    >
                      {node.name}
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-4">
                <h3 className="text-body font-medium text-text mb-3 flex items-center gap-2">
                  <Flag className="h-4 w-4 text-error" />
                  Terminal Nodes
                </h3>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {overview.terminal_nodes.length > 0 ? (
                    overview.terminal_nodes.map((node) => (
                      <div
                        key={node.id}
                        className="p-2 bg-error/10 rounded font-mono text-body-sm"
                      >
                        {node.name}
                      </div>
                    ))
                  ) : (
                    <p className="text-text-muted text-body-sm">No terminal nodes defined</p>
                  )}
                </div>
              </div>
            </div>

            {/* Test Actions */}
            <div className="card p-4">
              <h3 className="text-body font-medium text-text mb-4">Test Actions</h3>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={runTest}
                  disabled={running}
                  className="btn-primary"
                >
                  {running ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Simulate Flow
                </button>
                <button
                  onClick={createTestParticipant}
                  disabled={creatingParticipant}
                  className="btn-secondary"
                >
                  {creatingParticipant ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <UserPlus className="h-4 w-4" />
                  )}
                  Create Test Participant
                </button>
              </div>
              <p className="text-caption text-text-muted mt-2">
                &quot;Simulate Flow&quot; shows the message sequence without creating data.
                &quot;Create Test Participant&quot; enrolls a real test participant in the protocol.
              </p>
            </div>

            {/* Test Results */}
            {testResult && (
              <div className="card overflow-hidden">
                <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-surface">
                  <div>
                    <h3 className="text-title text-text">Protocol Flow Simulation</h3>
                    <p className="text-caption text-text-muted">
                      {testResult.total_nodes_in_flow} nodes in flow path |{' '}
                      ~{testResult.estimated_duration_days} days duration
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={expandAll} className="btn-ghost text-body-sm">
                      Expand All
                    </button>
                    <button onClick={collapseAll} className="btn-ghost text-body-sm">
                      Collapse All
                    </button>
                  </div>
                </div>

                {/* Flow Steps Timeline */}
                <div className="p-4">
                  <div className="relative">
                    {/* Timeline line */}
                    <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

                    {/* Steps */}
                    <div className="space-y-4">
                      {testResult.flow_steps.map((step, index) => {
                        const isExpanded = expandedSteps.has(index);
                        const isActive = activeStep === index;

                        return (
                          <div
                            key={step.node_id}
                            className={cn(
                              'relative pl-10 transition-all',
                              isActive && 'scale-[1.01]'
                            )}
                            onMouseEnter={() => setActiveStep(index)}
                            onMouseLeave={() => setActiveStep(null)}
                          >
                            {/* Timeline dot */}
                            <div
                              className={cn(
                                'absolute left-2 w-5 h-5 rounded-full flex items-center justify-center z-10',
                                step.is_entry
                                  ? 'bg-warning text-white'
                                  : step.is_terminal
                                    ? 'bg-error text-white'
                                    : 'bg-accent text-white'
                              )}
                            >
                              {step.is_entry ? (
                                <Zap className="h-3 w-3" />
                              ) : step.is_terminal ? (
                                <Flag className="h-3 w-3" />
                              ) : (
                                <span className="text-[10px] font-bold">{step.step}</span>
                              )}
                            </div>

                            {/* Step Card */}
                            <div
                              className={cn(
                                'card overflow-hidden cursor-pointer transition-shadow',
                                isExpanded && 'ring-2 ring-accent/20',
                                isActive && 'shadow-lg'
                              )}
                              onClick={() => toggleStep(index)}
                            >
                              <div className="p-3 flex items-center gap-3">
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4 text-text-muted flex-shrink-0" />
                                ) : (
                                  <ChevronRight className="h-4 w-4 text-text-muted flex-shrink-0" />
                                )}

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono font-medium text-text">
                                      {step.node_name}
                                    </span>
                                    {step.is_entry && (
                                      <span className="badge badge-warning text-[10px]">Entry</span>
                                    )}
                                    {step.is_terminal && (
                                      <span className="badge badge-error text-[10px]">Terminal</span>
                                    )}
                                  </div>
                                  {step.display_name && (
                                    <p className="text-caption text-text-muted truncate">
                                      {step.display_name}
                                    </p>
                                  )}
                                </div>

                                <div className="flex items-center gap-4 text-body-sm text-text-muted">
                                  <div className="flex items-center gap-1">
                                    <Clock className="h-3.5 w-3.5" />
                                    {new Date(step.scheduled_time).toLocaleTimeString([], {
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    })}
                                  </div>
                                  {step.edges.length > 0 && (
                                    <div className="flex items-center gap-1">
                                      <ArrowRight className="h-3.5 w-3.5" />
                                      {step.edges.length}
                                    </div>
                                  )}
                                </div>
                              </div>

                              {isExpanded && (
                                <div className="px-3 pb-3 pt-0 border-t border-border mt-0 space-y-3">
                                  {/* Message Preview */}
                                  {step.message_text && (
                                    <div className="mt-3">
                                      <p className="text-caption text-text-muted mb-1">Message:</p>
                                      <div className="p-3 bg-surface rounded-lg">
                                        <p className="text-body-sm text-text whitespace-pre-wrap">
                                          {step.message_text}
                                        </p>
                                      </div>
                                    </div>
                                  )}

                                  {/* Timing */}
                                  <div className="flex items-center gap-4 text-body-sm">
                                    <div>
                                      <span className="text-text-muted">Scheduled: </span>
                                      <span className="text-text">
                                        {new Date(step.scheduled_time).toLocaleString()}
                                      </span>
                                    </div>
                                    {step.delay_minutes && (
                                      <div>
                                        <span className="text-text-muted">Delay: </span>
                                        <span className="text-text">{step.delay_minutes} min</span>
                                      </div>
                                    )}
                                  </div>

                                  {/* Next Steps */}
                                  {step.edges.length > 0 && (
                                    <div>
                                      <p className="text-caption text-text-muted mb-2">
                                        Next steps:
                                      </p>
                                      <div className="flex flex-wrap gap-2">
                                        {step.edges.map((edge, edgeIndex) => (
                                          <div
                                            key={edgeIndex}
                                            className="flex items-center gap-2 px-2 py-1 bg-surface rounded text-body-sm"
                                          >
                                            <ArrowRight className="h-3 w-3 text-accent" />
                                            <span className="font-mono">{edge.to_node_name}</span>
                                            {edge.label && (
                                              <span className="text-text-muted">
                                                ({edge.label})
                                              </span>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Variables Used */}
                {testResult.variables.length > 0 && (
                  <div className="px-4 py-3 border-t border-border bg-surface">
                    <p className="text-caption text-text-muted mb-2">
                      Variables used in this protocol:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {testResult.variables.map((v) => (
                        <span
                          key={v.id}
                          className="px-2 py-1 bg-background rounded font-mono text-body-sm"
                          title={v.display_name || v.name}
                        >
                          {`{{${v.name}}}`}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* No Test Yet */}
            {!testResult && !running && (
              <div className="card p-8 text-center">
                <Play className="h-12 w-12 text-text-muted mx-auto mb-4" />
                <p className="text-body text-text-secondary mb-4">
                  Click &quot;Run Test&quot; or &quot;Simulate Flow&quot; to see the protocol message flow
                </p>
              </div>
            )}

            {/* Running State */}
            {running && (
              <div className="card p-8 text-center">
                <Loader2 className="h-12 w-12 animate-spin text-accent mx-auto mb-4" />
                <p className="text-body text-text-secondary">
                  Simulating protocol flow...
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="card p-8 text-center">
            <p className="text-body text-text-secondary">
              No protocol data found for this project.
            </p>
          </div>
        )}
      </div>
    </>
  );
}
