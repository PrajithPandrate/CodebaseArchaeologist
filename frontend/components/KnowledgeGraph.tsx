"use client";

import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";
import { useEffect } from "react";
import { GraphData } from "@/lib/types";

interface Props {
  data: GraphData;
  onNodeClick?: (nodeId: string, nodeType: string) => void;
}

const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  file: { bg: "#1e3a5f", border: "#3b82f6", text: "#93c5fd" },
  commit: { bg: "#1a3a2a", border: "#10b981", text: "#6ee7b7" },
  pull_request: { bg: "#2d1b4e", border: "#a855f7", text: "#c4b5fd" },
  issue: { bg: "#3b2a0e", border: "#f59e0b", text: "#fcd34d" },
  comment: { bg: "#0e2f3b", border: "#06b6d4", text: "#67e8f9" },
  author: { bg: "#1e293b", border: "#94a3b8", text: "#cbd5e1" },
};

const EDGE_COLORS: Record<string, string> = {
  modifies: "#3b82f6",
  includes: "#a855f7",
  fixes: "#10b981",
  references: "#f59e0b",
  discusses: "#06b6d4",
  depends_on: "#ef4444",
};

function buildFlowNodes(graphNodes: GraphData["nodes"]): Node[] {
  return graphNodes.map((n, i) => {
    const color = NODE_COLORS[n.type] || NODE_COLORS.author;
    return {
      id: n.id,
      position: {
        x: (i % 6) * 220 + Math.random() * 40,
        y: Math.floor(i / 6) * 140 + Math.random() * 40,
      },
      data: {
        label: (
          <div className="text-center">
            <div className="text-[10px] opacity-60 uppercase mb-0.5">{n.type}</div>
            <div className="text-xs font-medium truncate max-w-[120px]" title={n.label}>
              {n.label}
            </div>
          </div>
        ),
      },
      style: {
        background: color.bg,
        border: `1px solid ${color.border}`,
        color: color.text,
        borderRadius: "8px",
        padding: "8px 12px",
        minWidth: "120px",
        fontSize: "12px",
      },
    };
  });
}

function buildFlowEdges(graphEdges: GraphData["edges"]): Edge[] {
  return graphEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.type,
    labelStyle: { fontSize: 9, fill: "#64748b" },
    style: {
      stroke: EDGE_COLORS[e.type] || "#475569",
      strokeWidth: Math.max(1, e.confidence * 2),
      opacity: 0.7,
    },
    animated: e.type === "fixes",
  }));
}

export function KnowledgeGraph({ data, onNodeClick }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    setNodes(buildFlowNodes(data.nodes));
    setEdges(buildFlowEdges(data.edges));
  }, [data, setNodes, setEdges]);

  if (!data.nodes.length) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        No graph data. Try searching by file path or ingesting a repository first.
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={(_, node) => onNodeClick?.(node.id, node.type || "")}
      fitView
      attributionPosition="bottom-left"
      style={{ background: "hsl(222 47% 6%)" }}
    >
      <Background color="hsl(222 47% 12%)" variant={BackgroundVariant.Dots} gap={20} size={1} />
      <Controls
        style={{
          background: "hsl(222 47% 9%)",
          border: "1px solid hsl(222 47% 15%)",
        }}
      />
      <MiniMap
        style={{
          background: "hsl(222 47% 9%)",
          border: "1px solid hsl(222 47% 15%)",
        }}
        nodeColor={(n) => {
          const t = (n.data as { type?: string })?.type || "";
          return NODE_COLORS[t]?.border || "#475569";
        }}
      />
    </ReactFlow>
  );
}
