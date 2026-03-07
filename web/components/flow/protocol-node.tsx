"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Play, Square, MessageSquare, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ProtocolNodeData {
  nodeId: number;
  name: string;
  displayName: string | null;
  isEntry: boolean;
  isTerminal: boolean;
  templateName: string | null;
  timingElementId: number | null;
  nodeOrder: number;
  incomingCount: number;
  outgoingCount: number;
  [key: string]: unknown;
}

function ProtocolNodeComponent({ data }: NodeProps) {
  const d = data as unknown as ProtocolNodeData;

  return (
    <div
      className={cn(
        "rounded-lg border-2 bg-white shadow-sm min-w-[180px] max-w-[220px] transition-shadow hover:shadow-md",
        d.isEntry && "border-emerald-500",
        d.isTerminal && "border-red-500",
        !d.isEntry && !d.isTerminal && "border-slate-300",
      )}
    >
      {/* Incoming handle */}
      {!d.isEntry && (
        <Handle
          type="target"
          position={Position.Top}
          className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white"
        />
      )}

      {/* Header */}
      <div
        className={cn(
          "px-3 py-1.5 flex items-center gap-1.5 rounded-t-md text-xs font-medium",
          d.isEntry && "bg-emerald-50 text-emerald-700",
          d.isTerminal && "bg-red-50 text-red-700",
          !d.isEntry && !d.isTerminal && "bg-slate-50 text-slate-600",
        )}
      >
        {d.isEntry && <Play className="h-3 w-3" />}
        {d.isTerminal && <Square className="h-3 w-3" />}
        {!d.isEntry && !d.isTerminal && <MessageSquare className="h-3 w-3" />}
        <span>#{d.nodeOrder}</span>
        {d.isEntry && <span className="ml-auto">Entry</span>}
        {d.isTerminal && <span className="ml-auto">Terminal</span>}
      </div>

      {/* Body */}
      <div className="px-3 py-2">
        <p className="text-sm font-semibold text-slate-900 truncate">
          {d.displayName || d.name}
        </p>
        {d.displayName && (
          <p className="text-xs text-slate-500 font-mono truncate">{d.name}</p>
        )}
      </div>

      {/* Footer - template info */}
      {(d.templateName || d.timingElementId) && (
        <div className="px-3 pb-2 flex flex-col gap-1">
          {d.templateName && (
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <MessageSquare className="h-3 w-3 flex-shrink-0" />
              <span className="truncate">{d.templateName}</span>
            </div>
          )}
          {d.timingElementId && (
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <Clock className="h-3 w-3 flex-shrink-0" />
              <span>Timing #{d.timingElementId}</span>
            </div>
          )}
        </div>
      )}

      {/* Outgoing handle */}
      {!d.isTerminal && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white"
        />
      )}
    </div>
  );
}

export const ProtocolNode = memo(ProtocolNodeComponent);
