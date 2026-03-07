"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node as RFNode,
  type Edge as RFEdge,
  type NodeMouseHandler,
  MarkerType,
  BackgroundVariant,
} from "@xyflow/react";
import dagre from "dagre";
import "@xyflow/react/dist/style.css";

import { ProtocolNode, type ProtocolNodeData } from "./protocol-node";
import type {
  Node as ApiNode,
  Edge as ApiEdge,
  Template,
} from "@/lib/api";

const NODE_WIDTH = 200;
const NODE_HEIGHT = 100;

const nodeTypes = { protocol: ProtocolNode };

function layoutGraph(
  rfNodes: RFNode[],
  rfEdges: RFEdge[],
  direction: "TB" | "LR" = "TB",
): RFNode[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, nodesep: 60, ranksep: 80 });

  rfNodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  rfEdges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  return rfNodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });
}

interface ProtocolFlowProps {
  apiNodes: ApiNode[];
  apiEdges: ApiEdge[];
  templateMap: Map<number, Template>;
  onNodeClick?: (nodeId: number) => void;
}

export function ProtocolFlow({
  apiNodes,
  apiEdges,
  templateMap,
  onNodeClick,
}: ProtocolFlowProps) {
  // Build edge lookup for counts
  const edgeCounts = useMemo(() => {
    const counts: Record<number, { incoming: number; outgoing: number }> = {};
    apiNodes.forEach((n) => {
      counts[n.id] = { incoming: 0, outgoing: 0 };
    });
    apiEdges.forEach((e) => {
      if (counts[e.parent_node_id]) counts[e.parent_node_id].outgoing++;
      if (counts[e.child_node_id]) counts[e.child_node_id].incoming++;
    });
    return counts;
  }, [apiNodes, apiEdges]);

  // Convert API data → React Flow data
  const { initialNodes, initialEdges } = useMemo(() => {
    const rfNodes: RFNode[] = apiNodes.map((node) => ({
      id: String(node.id),
      type: "protocol",
      position: { x: 0, y: 0 },
      data: {
        nodeId: node.id,
        name: node.name,
        displayName: node.display_name,
        isEntry: node.is_entry_node,
        isTerminal: node.is_terminal_node,
        templateName: node.template_id
          ? templateMap.get(node.template_id)?.name ?? null
          : null,
        timingElementId: node.timing_element_id,
        nodeOrder: node.node_order,
        incomingCount: edgeCounts[node.id]?.incoming ?? 0,
        outgoingCount: edgeCounts[node.id]?.outgoing ?? 0,
      } satisfies ProtocolNodeData,
    }));

    const rfEdges: RFEdge[] = apiEdges.map((edge) => ({
      id: String(edge.id),
      source: String(edge.parent_node_id),
      target: String(edge.child_node_id),
      label: edge.edge_label || undefined,
      type: "smoothstep",
      animated: false,
      markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
      style: { strokeWidth: 2, stroke: "#94a3b8" },
      labelStyle: {
        fontSize: 11,
        fontWeight: 500,
        fill: "#64748b",
      },
      labelBgStyle: {
        fill: "#f8fafc",
        fillOpacity: 0.9,
      },
    }));

    const layoutedNodes = layoutGraph(rfNodes, rfEdges);

    return { initialNodes: layoutedNodes, initialEdges: rfEdges };
  }, [apiNodes, apiEdges, templateMap, edgeCounts]);

  const [flowNodes, , onNodesChange] = useNodesState(initialNodes);
  const [flowEdges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      const data = node.data as unknown as ProtocolNodeData;
      onNodeClick?.(data.nodeId);
    },
    [onNodeClick],
  );

  const miniMapNodeColor = useCallback((node: RFNode) => {
    const data = node.data as unknown as ProtocolNodeData;
    if (data.isEntry) return "#10b981";
    if (data.isTerminal) return "#ef4444";
    return "#94a3b8";
  }, []);

  if (apiNodes.length === 0) {
    return null;
  }

  return (
    <div className="h-[calc(100vh-280px)] min-h-[500px] border border-border rounded-lg overflow-hidden bg-white">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#e2e8f0" />
        <Controls
          showInteractive={false}
          className="!bg-white !border-slate-200 !shadow-sm"
        />
        <MiniMap
          nodeColor={miniMapNodeColor}
          maskColor="rgba(0, 0, 0, 0.08)"
          className="!bg-white !border-slate-200"
          pannable
          zoomable
        />
      </ReactFlow>
    </div>
  );
}
