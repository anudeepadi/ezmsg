'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { nodes, Node, Edge, GraphResponse, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Plus,
  Search,
  GitBranch,
  ArrowRight,
  Play,
  Square,
  MoreHorizontal,
  Pencil,
  Trash2,
  Link as LinkIcon,
} from 'lucide-react';

export default function NodesPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [openMenu, setOpenMenu] = useState<number | null>(null);

  useEffect(() => {
    loadGraph();
  }, [projectId]);

  async function loadGraph() {
    try {
      const data = await nodes.getGraph(projectId);
      setGraph(data);
    } catch (err) {
      addToast('error', 'Failed to load nodes');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(nodeId: number) {
    if (!confirm('Are you sure you want to delete this node?')) return;

    try {
      await nodes.delete(nodeId);
      addToast('success', 'Node deleted');
      loadGraph();
    } catch (err) {
      addToast('error', 'Failed to delete node');
    }
    setOpenMenu(null);
  }

  const filteredNodes = graph?.nodes.filter(
    (n) =>
      n.name.toLowerCase().includes(search.toLowerCase()) ||
      n.display_name?.toLowerCase().includes(search.toLowerCase())
  ) || [];

  // Create edge lookup map
  const nodeEdges = new Map<number, { outgoing: Edge[]; incoming: Edge[] }>();
  graph?.nodes.forEach((node) => {
    nodeEdges.set(node.id, { outgoing: [], incoming: [] });
  });
  graph?.edges.forEach((edge) => {
    const parentData = nodeEdges.get(edge.parent_node_id);
    const childData = nodeEdges.get(edge.child_node_id);
    if (parentData) parentData.outgoing.push(edge);
    if (childData) childData.incoming.push(edge);
  });

  return (
    <>
      <Header
        title="Messaging Nodes"
        description={`${graph?.nodes.length || 0} nodes, ${graph?.edges.length || 0} edges`}
        actions={
          <div className="flex items-center gap-3">
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <Link
              href={`/admin/projects/${projectId}/nodes/new`}
              className="btn-primary"
            >
              <Plus className="h-4 w-4" />
              Add Node
            </Link>
          </div>
        }
      />

      <div className="p-6">
        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
        </div>

        {/* Table */}
        <div className="card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
            </div>
          ) : filteredNodes.length === 0 ? (
            <div className="p-8 text-center">
              <GitBranch className="h-12 w-12 text-text-muted mx-auto mb-4" />
              <p className="text-body text-text-secondary mb-4">
                {search ? 'No nodes match your search' : 'No nodes defined yet'}
              </p>
              {!search && (
                <Link
                  href={`/admin/projects/${projectId}/nodes/new`}
                  className="btn-primary"
                >
                  <Plus className="h-4 w-4" />
                  Create first node
                </Link>
              )}
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Node</th>
                  <th>Type</th>
                  <th>Template</th>
                  <th>Connections</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {filteredNodes
                  .sort((a, b) => a.node_order - b.node_order)
                  .map((node) => {
                    const edges = nodeEdges.get(node.id);
                    return (
                      <tr key={node.id}>
                        <td className="text-text-muted font-mono">
                          {node.node_order}
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            {node.is_entry_node && (
                              <Play className="h-4 w-4 text-success" />
                            )}
                            {node.is_terminal_node && (
                              <Square className="h-4 w-4 text-error" />
                            )}
                            <div>
                              <p className="font-medium text-text">
                                {node.display_name || node.name}
                              </p>
                              <p className="text-caption text-text-muted font-mono">
                                {node.name}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="flex gap-2">
                            {node.is_entry_node && (
                              <span className="badge badge-success">Entry</span>
                            )}
                            {node.is_terminal_node && (
                              <span className="badge badge-error">Terminal</span>
                            )}
                            {!node.is_entry_node && !node.is_terminal_node && (
                              <span className="badge badge-default">Standard</span>
                            )}
                          </div>
                        </td>
                        <td className="text-text-secondary">
                          {node.template_id ? `#${node.template_id}` : '-'}
                        </td>
                        <td>
                          <div className="flex items-center gap-3 text-body-sm">
                            <span className="text-text-secondary">
                              {edges?.incoming.length || 0} in
                            </span>
                            <ArrowRight className="h-4 w-4 text-text-muted" />
                            <span className="text-text-secondary">
                              {edges?.outgoing.length || 0} out
                            </span>
                          </div>
                        </td>
                        <td>
                          <div className="relative">
                            <button
                              onClick={() =>
                                setOpenMenu(openMenu === node.id ? null : node.id)
                              }
                              className="btn-ghost p-2"
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </button>

                            {openMenu === node.id && (
                              <>
                                <div
                                  className="fixed inset-0 z-10"
                                  onClick={() => setOpenMenu(null)}
                                />
                                <div className="absolute right-0 top-full mt-1 w-48 bg-surface border border-border rounded-lg shadow-elevated z-20 py-1">
                                  <Link
                                    href={`/admin/projects/${projectId}/nodes/${node.id}/edit`}
                                    className="flex items-center gap-2 px-4 py-2 text-body-sm text-text hover:bg-background transition-colors"
                                  >
                                    <Pencil className="h-4 w-4" />
                                    Edit
                                  </Link>
                                  <Link
                                    href={`/admin/projects/${projectId}/nodes/${node.id}/edges`}
                                    className="flex items-center gap-2 px-4 py-2 text-body-sm text-text hover:bg-background transition-colors"
                                  >
                                    <LinkIcon className="h-4 w-4" />
                                    Manage Edges
                                  </Link>
                                  <div className="border-t border-border my-1" />
                                  <button
                                    onClick={() => handleDelete(node.id)}
                                    className="flex items-center gap-2 px-4 py-2 text-body-sm text-error hover:bg-background transition-colors w-full text-left"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                    Delete
                                  </button>
                                </div>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          )}
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center gap-6 text-body-sm text-text-secondary">
          <div className="flex items-center gap-2">
            <Play className="h-4 w-4 text-success" />
            Entry Node
          </div>
          <div className="flex items-center gap-2">
            <Square className="h-4 w-4 text-error" />
            Terminal Node
          </div>
        </div>
      </div>
    </>
  );
}
