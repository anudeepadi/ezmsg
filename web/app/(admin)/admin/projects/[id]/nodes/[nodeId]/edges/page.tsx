'use client';

import { useState, useEffect, useMemo, FormEvent } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { nodes, Node, Edge, GraphResponse, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { ArrowLeft, Plus, Trash2, ArrowRight, ArrowDown } from 'lucide-react';

export default function ManageEdgesPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const nodeId = Number(params.nodeId);
  const { addToast } = useToastStore();

  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const [targetNodeId, setTargetNodeId] = useState<string>('');
  const [edgeLabel, setEdgeLabel] = useState('');
  const [edgeOrder, setEdgeOrder] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const backUrl = `/admin/projects/${projectId}/nodes`;

  useEffect(() => {
    loadGraph();
  }, [projectId]);

  async function loadGraph() {
    try {
      const data = await nodes.getGraph(projectId);
      setGraph(data);
    } catch {
      addToast('error', 'Failed to load graph data');
    } finally {
      setLoading(false);
    }
  }

  const currentNode = useMemo(() => {
    return graph?.nodes.find((n) => n.id === nodeId) || null;
  }, [graph, nodeId]);

  const incomingEdges = useMemo(() => {
    if (!graph) return [];
    return graph.edges.filter((e) => e.child_node_id === nodeId);
  }, [graph, nodeId]);

  const outgoingEdges = useMemo(() => {
    if (!graph) return [];
    return graph.edges.filter((e) => e.parent_node_id === nodeId);
  }, [graph, nodeId]);

  const availableTargetNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes
      .filter((n) => n.id !== nodeId)
      .sort((a, b) => a.node_order - b.node_order);
  }, [graph, nodeId]);

  function getNodeName(id: number): string {
    const node = graph?.nodes.find((n) => n.id === id);
    return node?.display_name || node?.name || `Node #${id}`;
  }

  async function handleAddEdge(e: FormEvent) {
    e.preventDefault();

    if (!targetNodeId) {
      addToast('error', 'Please select a target node');
      return;
    }

    setIsSubmitting(true);

    try {
      await nodes.createEdge({
        parent_node_id: nodeId,
        child_node_id: Number(targetNodeId),
        edge_label: edgeLabel || undefined,
        edge_order: edgeOrder,
      });
      addToast('success', 'Edge created successfully');
      setTargetNodeId('');
      setEdgeLabel('');
      setEdgeOrder(0);
      await loadGraph();
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || 'Failed to create edge'
          : 'Failed to create edge';
      addToast('error', message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteEdge(edgeId: number) {
    if (!confirm('Are you sure you want to delete this edge?')) return;

    try {
      await nodes.deleteEdge(edgeId);
      addToast('success', 'Edge deleted');
      await loadGraph();
    } catch {
      addToast('error', 'Failed to delete edge');
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Loading..." />
        <div className="p-6">
          <div className="animate-pulse space-y-6">
            <div className="h-64 bg-surface rounded-lg" />
          </div>
        </div>
      </>
    );
  }

  const nodeName = currentNode?.display_name || currentNode?.name || `Node #${nodeId}`;

  return (
    <>
      <Header
        title="Manage Edges"
        description={`Connections for "${nodeName}"`}
        actions={
          <Link href={backUrl} className="btn-secondary">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        }
      />

      <div className="p-6 max-w-4xl space-y-6">
        {/* Incoming Edges */}
        <div className="card overflow-hidden">
          <div className="px-6 py-4 bg-surface border-b border-border">
            <div className="flex items-center gap-2">
              <ArrowDown className="h-4 w-4 text-text-muted" />
              <h3 className="text-title text-text">
                Incoming Edges
              </h3>
              <span className="badge badge-default">{incomingEdges.length}</span>
            </div>
          </div>

          {incomingEdges.length === 0 ? (
            <div className="p-6 text-center text-text-secondary">
              No incoming edges. This may be an entry node.
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>From Node</th>
                  <th>Edge Label</th>
                  <th>Order</th>
                </tr>
              </thead>
              <tbody>
                {incomingEdges.map((edge) => (
                  <tr key={edge.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-text">
                          {getNodeName(edge.parent_node_id)}
                        </span>
                        <ArrowRight className="h-4 w-4 text-text-muted" />
                        <span className="text-text-muted text-body-sm">here</span>
                      </div>
                    </td>
                    <td className="text-text-secondary">
                      {edge.edge_label || '-'}
                    </td>
                    <td className="text-text-secondary font-mono">
                      {edge.edge_order}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Outgoing Edges */}
        <div className="card overflow-hidden">
          <div className="px-6 py-4 bg-surface border-b border-border">
            <div className="flex items-center gap-2">
              <ArrowRight className="h-4 w-4 text-text-muted" />
              <h3 className="text-title text-text">
                Outgoing Edges
              </h3>
              <span className="badge badge-default">{outgoingEdges.length}</span>
            </div>
          </div>

          {outgoingEdges.length === 0 ? (
            <div className="p-6 text-center text-text-secondary">
              No outgoing edges. This may be a terminal node.
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>To Node</th>
                  <th>Edge Label</th>
                  <th>Order</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {outgoingEdges.map((edge) => (
                  <tr key={edge.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className="text-text-muted text-body-sm">here</span>
                        <ArrowRight className="h-4 w-4 text-text-muted" />
                        <span className="font-medium text-text">
                          {getNodeName(edge.child_node_id)}
                        </span>
                      </div>
                    </td>
                    <td className="text-text-secondary">
                      {edge.edge_label || '-'}
                    </td>
                    <td className="text-text-secondary font-mono">
                      {edge.edge_order}
                    </td>
                    <td>
                      <button
                        onClick={() => handleDeleteEdge(edge.id)}
                        className="btn-ghost p-1.5 text-error"
                        title="Delete edge"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Add Edge Form */}
        <div className="card p-6 space-y-6">
          <div className="flex items-center gap-2">
            <Plus className="h-5 w-5 text-text-muted" />
            <h3 className="text-title text-text">Add Outgoing Edge</h3>
          </div>

          <form onSubmit={handleAddEdge} className="space-y-4">
            <div>
              <label htmlFor="targetNode" className="label">
                Target Node <span className="text-error">*</span>
              </label>
              <select
                id="targetNode"
                value={targetNodeId}
                onChange={(e) => setTargetNodeId(e.target.value)}
                className="input"
                required
              >
                <option value="">Select a node...</option>
                {availableTargetNodes.map((node) => (
                  <option key={node.id} value={node.id}>
                    {node.display_name || node.name} (#{node.node_order})
                  </option>
                ))}
              </select>
              <p className="text-caption text-text-muted mt-1.5">
                The node this edge will connect to from the current node.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edgeLabel" className="label">Edge Label</label>
                <input
                  id="edgeLabel"
                  type="text"
                  value={edgeLabel}
                  onChange={(e) => setEdgeLabel(e.target.value)}
                  className="input"
                  placeholder="e.g., YES, NO, DEFAULT"
                />
                <p className="text-caption text-text-muted mt-1.5">
                  Optional label to identify this path.
                </p>
              </div>

              <div>
                <label htmlFor="edgeOrder" className="label">Edge Order</label>
                <input
                  id="edgeOrder"
                  type="number"
                  value={edgeOrder}
                  onChange={(e) => setEdgeOrder(Number(e.target.value))}
                  className="input"
                  min={0}
                />
                <p className="text-caption text-text-muted mt-1.5">
                  Determines evaluation priority (lower first).
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-border">
              <button type="submit" disabled={isSubmitting} className="btn-primary">
                <Plus className="h-4 w-4" />
                {isSubmitting ? 'Adding...' : 'Add Edge'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
