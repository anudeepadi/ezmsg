'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { nodes, templates, Node, Edge, GraphResponse, Template, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Plus,
  Search,
  GitBranch,
  ArrowRight,
  ArrowDown,
  Play,
  Square,
  MoreHorizontal,
  Pencil,
  Trash2,
  Link as LinkIcon,
  List,
  Network,
  MessageSquare,
  Clock,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
} from 'lucide-react';

type ViewMode = 'list' | 'flow';

export default function NodesPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [templateList, setTemplateList] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [openMenu, setOpenMenu] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('flow');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['INTAKE', 'Q1', 'Q2', 'Q3']));

  useEffect(() => {
    loadData();
  }, [projectId]);

  async function loadData() {
    try {
      const [graphData, templateData] = await Promise.all([
        nodes.getGraph(projectId),
        templates.list(projectId),
      ]);
      setGraph(graphData);
      setTemplateList(templateData);
    } catch (err) {
      addToast('error', 'Failed to load nodes');
    } finally {
      setLoading(false);
    }
  }

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

  // Create template lookup
  const templateMap = useMemo(() => {
    return new Map(templateList.map((t) => [t.id, t]));
  }, [templateList]);

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

  // Group nodes by prefix for flow view
  const groupedNodes = useMemo(() => {
    const groups: Record<string, Node[]> = {};
    filteredNodes.forEach((node) => {
      const prefix = node.name.split('_')[0] || 'Other';
      if (!groups[prefix]) groups[prefix] = [];
      groups[prefix].push(node);
    });
    // Sort nodes within each group by node_order
    Object.keys(groups).forEach((key) => {
      groups[key].sort((a, b) => a.node_order - b.node_order);
    });
    return groups;
  }, [filteredNodes]);

  const toggleGroup = (group: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(group)) {
        next.delete(group);
      } else {
        next.add(group);
      }
      return next;
    });
  };

  // Get node name by ID for displaying connections
  const getNodeName = (nodeId: number) => {
    const node = graph?.nodes.find((n) => n.id === nodeId);
    return node?.display_name || node?.name || `Node #${nodeId}`;
  };

  return (
    <>
      <Header
        title="Messaging Nodes"
        description={`${graph?.nodes.length || 0} nodes, ${graph?.edges.length || 0} edges`}
        actions={
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-surface border border-border rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'px-3 py-1.5 rounded text-body-sm flex items-center gap-1.5 transition-colors',
                  viewMode === 'list'
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:text-text'
                )}
              >
                <List className="h-4 w-4" />
                List
              </button>
              <button
                onClick={() => setViewMode('flow')}
                className={cn(
                  'px-3 py-1.5 rounded text-body-sm flex items-center gap-1.5 transition-colors',
                  viewMode === 'flow'
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:text-text'
                )}
              >
                <Network className="h-4 w-4" />
                Flow
              </button>
            </div>
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

        {/* Content Area */}
        {loading ? (
          <div className="card p-8 text-center">
            <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
          </div>
        ) : filteredNodes.length === 0 ? (
          <div className="card p-8 text-center">
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
        ) : viewMode === 'list' ? (
          /* List View - Table */
          <div className="card overflow-hidden">
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
                    const template = node.template_id ? templateMap.get(node.template_id) : null;
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
                          {template ? (
                            <span className="text-body-sm">{template.name}</span>
                          ) : node.template_id ? (
                            <span className="text-text-muted">#{node.template_id}</span>
                          ) : (
                            '-'
                          )}
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
          </div>
        ) : (
          /* Flow View - Visual Groups */
          <div className="space-y-4">
            {Object.entries(groupedNodes).map(([group, nodes]) => (
              <div key={group} className="card overflow-hidden">
                {/* Group Header */}
                <button
                  onClick={() => toggleGroup(group)}
                  className="w-full px-4 py-3 bg-surface flex items-center justify-between hover:bg-background transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedGroups.has(group) ? (
                      <ChevronDown className="h-5 w-5 text-text-muted" />
                    ) : (
                      <ChevronRightIcon className="h-5 w-5 text-text-muted" />
                    )}
                    <h3 className="text-title text-text">{group}</h3>
                    <span className="badge badge-default">{nodes.length} nodes</span>
                  </div>
                  <div className="flex items-center gap-2 text-body-sm text-text-muted">
                    {nodes.some((n) => n.is_entry_node) && (
                      <span className="flex items-center gap-1">
                        <Play className="h-3 w-3 text-success" /> Entry
                      </span>
                    )}
                    {nodes.some((n) => n.is_terminal_node) && (
                      <span className="flex items-center gap-1">
                        <Square className="h-3 w-3 text-error" /> Terminal
                      </span>
                    )}
                  </div>
                </button>

                {/* Group Content */}
                {expandedGroups.has(group) && (
                  <div className="p-4 border-t border-border">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {nodes.map((node) => {
                        const edges = nodeEdges.get(node.id);
                        const template = node.template_id ? templateMap.get(node.template_id) : null;
                        return (
                          <div
                            key={node.id}
                            className={cn(
                              'border rounded-lg p-4 transition-all hover:shadow-md',
                              node.is_entry_node && 'border-success bg-success/5',
                              node.is_terminal_node && 'border-error bg-error/5',
                              !node.is_entry_node && !node.is_terminal_node && 'border-border'
                            )}
                          >
                            {/* Node Header */}
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center gap-2">
                                {node.is_entry_node && (
                                  <Play className="h-4 w-4 text-success" />
                                )}
                                {node.is_terminal_node && (
                                  <Square className="h-4 w-4 text-error" />
                                )}
                                {!node.is_entry_node && !node.is_terminal_node && (
                                  <MessageSquare className="h-4 w-4 text-accent" />
                                )}
                                <span className="font-mono text-caption text-text-muted">
                                  #{node.node_order}
                                </span>
                              </div>
                              <div className="relative">
                                <button
                                  onClick={() =>
                                    setOpenMenu(openMenu === node.id ? null : node.id)
                                  }
                                  className="btn-ghost p-1"
                                >
                                  <MoreHorizontal className="h-4 w-4" />
                                </button>
                                {openMenu === node.id && (
                                  <>
                                    <div
                                      className="fixed inset-0 z-10"
                                      onClick={() => setOpenMenu(null)}
                                    />
                                    <div className="absolute right-0 top-full mt-1 w-40 bg-surface border border-border rounded-lg shadow-elevated z-20 py-1">
                                      <Link
                                        href={`/admin/projects/${projectId}/nodes/${node.id}/edit`}
                                        className="flex items-center gap-2 px-3 py-1.5 text-body-sm text-text hover:bg-background transition-colors"
                                      >
                                        <Pencil className="h-3 w-3" />
                                        Edit
                                      </Link>
                                      <Link
                                        href={`/admin/projects/${projectId}/nodes/${node.id}/edges`}
                                        className="flex items-center gap-2 px-3 py-1.5 text-body-sm text-text hover:bg-background transition-colors"
                                      >
                                        <LinkIcon className="h-3 w-3" />
                                        Edges
                                      </Link>
                                      <button
                                        onClick={() => handleDelete(node.id)}
                                        className="flex items-center gap-2 px-3 py-1.5 text-body-sm text-error hover:bg-background transition-colors w-full text-left"
                                      >
                                        <Trash2 className="h-3 w-3" />
                                        Delete
                                      </button>
                                    </div>
                                  </>
                                )}
                              </div>
                            </div>

                            {/* Node Name */}
                            <h4 className="font-medium text-text mb-1">
                              {node.display_name || node.name}
                            </h4>
                            <p className="text-caption text-text-muted font-mono mb-3">
                              {node.name}
                            </p>

                            {/* Template Info */}
                            {template && (
                              <div className="mb-3 p-2 bg-surface rounded text-body-sm">
                                <div className="flex items-center gap-1.5 text-text-muted mb-1">
                                  <MessageSquare className="h-3 w-3" />
                                  <span>Template</span>
                                </div>
                                <p className="text-text truncate">{template.name}</p>
                              </div>
                            )}

                            {/* Timing Info */}
                            {node.timing_element_id && (
                              <div className="mb-3 flex items-center gap-1.5 text-body-sm text-text-muted">
                                <Clock className="h-3 w-3" />
                                <span>Timing #{node.timing_element_id}</span>
                              </div>
                            )}

                            {/* Connections */}
                            <div className="pt-3 border-t border-border">
                              <div className="flex items-center justify-between text-body-sm">
                                <div className="flex items-center gap-1 text-text-muted">
                                  <ArrowDown className="h-3 w-3" />
                                  <span>{edges?.incoming.length || 0} incoming</span>
                                </div>
                                <div className="flex items-center gap-1 text-text-muted">
                                  <span>{edges?.outgoing.length || 0} outgoing</span>
                                  <ArrowRight className="h-3 w-3" />
                                </div>
                              </div>
                              {/* Show outgoing connections */}
                              {edges && edges.outgoing.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-1">
                                  {edges.outgoing.slice(0, 3).map((edge) => (
                                    <span
                                      key={edge.id}
                                      className="text-xs px-2 py-0.5 bg-accent/10 text-accent rounded"
                                      title={edge.edge_label || 'Default'}
                                    >
                                      → {getNodeName(edge.child_node_id).slice(0, 15)}
                                    </span>
                                  ))}
                                  {edges.outgoing.length > 3 && (
                                    <span className="text-xs px-2 py-0.5 bg-surface text-text-muted rounded">
                                      +{edges.outgoing.length - 3} more
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

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
