"use client";

import React, { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Handle,
  Position,
  NodeProps,
  MarkerType,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import {
  Database,
  Server,
  Globe,
  Shield,
  HardDrive,
  Layers,
  Maximize2,
  Minimize2,
  Code2,
  Eye,
  Cpu,
  Cloud,
  Lock,
  Zap,
  Box,
  RefreshCw,
  MessageSquare,
} from "lucide-react";
import { MermaidViewer } from "@/components/design/mermaid-viewer";

/* ─────────────────── Icon mapping ─────────────────── */
const ICON_MAP: Record<string, React.ElementType> = {
  database: Database,
  db: Database,
  postgres: Database,
  postgresql: Database,
  mysql: Database,
  mongo: Database,
  mongodb: Database,
  redis: Zap,
  cache: Zap,
  memcached: Zap,
  api: Server,
  backend: Server,
  server: Server,
  service: Server,
  microservice: Server,
  gateway: Globe,
  "api gateway": Globe,
  "load balancer": Globe,
  lb: Globe,
  nginx: Globe,
  cdn: Cloud,
  frontend: Layers,
  client: Layers,
  web: Layers,
  app: Layers,
  ui: Layers,
  auth: Shield,
  authentication: Shield,
  authorization: Lock,
  security: Lock,
  queue: MessageSquare,
  kafka: MessageSquare,
  rabbitmq: MessageSquare,
  sqs: MessageSquare,
  worker: Cpu,
  "background worker": Cpu,
  cron: Cpu,
  storage: HardDrive,
  s3: HardDrive,
  blob: HardDrive,
  docker: Box,
  container: Box,
  kubernetes: Box,
  k8s: Box,
};

function getNodeIcon(label: string): React.ElementType {
  const lower = label.toLowerCase();
  for (const [keyword, icon] of Object.entries(ICON_MAP)) {
    if (lower.includes(keyword)) return icon;
  }
  return Server;
}

const NODE_COLORS: Record<string, { bg: string; border: string; glow: string }> = {
  database: { bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.3)", glow: "0 0 20px rgba(56,189,248,0.15)" },
  cache: { bg: "rgba(250,204,21,0.08)", border: "rgba(250,204,21,0.3)", glow: "0 0 20px rgba(250,204,21,0.15)" },
  gateway: { bg: "rgba(168,85,247,0.08)", border: "rgba(168,85,247,0.3)", glow: "0 0 20px rgba(168,85,247,0.15)" },
  queue: { bg: "rgba(251,146,60,0.08)", border: "rgba(251,146,60,0.3)", glow: "0 0 20px rgba(251,146,60,0.15)" },
  auth: { bg: "rgba(34,197,94,0.08)", border: "rgba(34,197,94,0.3)", glow: "0 0 20px rgba(34,197,94,0.15)" },
  storage: { bg: "rgba(244,114,182,0.08)", border: "rgba(244,114,182,0.3)", glow: "0 0 20px rgba(244,114,182,0.15)" },
  default: { bg: "rgba(255,255,255,0.04)", border: "rgba(255,255,255,0.12)", glow: "0 0 20px rgba(255,255,255,0.05)" },
};

function getNodeColor(label: string) {
  const lower = label.toLowerCase();
  if (lower.match(/database|db|postgres|mysql|mongo/)) return NODE_COLORS.database;
  if (lower.match(/cache|redis|memcached/)) return NODE_COLORS.cache;
  if (lower.match(/gateway|load.?balancer|cdn|nginx|lb/)) return NODE_COLORS.gateway;
  if (lower.match(/queue|kafka|rabbit|sqs|event/)) return NODE_COLORS.queue;
  if (lower.match(/auth|security|lock/)) return NODE_COLORS.auth;
  if (lower.match(/storage|s3|blob|file/)) return NODE_COLORS.storage;
  return NODE_COLORS.default;
}

/* ─────────────── Custom Node Component ─────────────── */
function ArchitectureNode({ data }: NodeProps) {
  const Icon = data.icon as React.ElementType;
  const colors = data.colors as { bg: string; border: string; glow: string };

  return (
    <div
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        boxShadow: colors.glow,
        borderRadius: "16px",
        padding: "16px 20px",
        minWidth: "160px",
        maxWidth: "220px",
        backdropFilter: "blur(12px)",
        cursor: "grab",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: colors.border, width: 8, height: 8, border: "2px solid #0a0a0a" }} />
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 32,
            height: 32,
            borderRadius: 10,
            background: "rgba(255,255,255,0.06)",
            border: `1px solid ${colors.border}`,
            flexShrink: 0,
          }}
        >
          <Icon style={{ width: 16, height: 16, color: colors.border }} />
        </div>
        <span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.85)", lineHeight: 1.3, wordBreak: "break-word" }}>
          {data.label as string}
        </span>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ background: colors.border, width: 8, height: 8, border: "2px solid #0a0a0a" }} />
    </div>
  );
}

const nodeTypes = { architecture: ArchitectureNode };

/* ─────────────── Mermaid Parser ─────────────── */
function parseMermaidToFlow(mermaid: string): { nodes: Node[]; edges: Edge[] } {
  const lines = mermaid.split("\n").map((l) => l.trim()).filter(Boolean);
  const nodeMap = new Map<string, string>(); // id → label
  const edges: Edge[] = [];

  // Extract node definitions and edges
  for (const line of lines) {
    // Skip graph/flowchart directives, subgraph, end, style, classDef
    if (/^(graph|flowchart|subgraph|end|style|classDef|class\s)/i.test(line)) continue;
    if (/^%%/.test(line)) continue;

    // Match edges: A --> B, A -->|label| B, A --- B, A ==> B, etc.
    const edgeMatch = line.match(
      /^(\w+)(?:\[([^\]]*)\]|(?:\([^)]*\))|(?:\{[^}]*\})|(?:>([^\]]*)\]))?\s*(-->|==>|-.->|---|-.-|-->\|[^|]*\||==>|<-->)\s*(?:\|([^|]*)\|)?\s*(\w+)(?:\[([^\]]*)\]|(?:\(([^)]*)\))|(?:\{([^}]*)\})|(?:>([^\]]*)\]))?/
    );

    if (edgeMatch) {
      const sourceId = edgeMatch[1];
      const sourceLabel = edgeMatch[2] || edgeMatch[3];
      const edgeType = edgeMatch[4];
      const edgeLabel = edgeMatch[5] || (edgeType.includes("|") ? edgeType.match(/\|([^|]*)\|/)?.[1] : undefined);
      const targetId = edgeMatch[6];
      const targetLabel = edgeMatch[7] || edgeMatch[8] || edgeMatch[9] || edgeMatch[10];

      if (sourceLabel && !nodeMap.has(sourceId)) nodeMap.set(sourceId, sourceLabel);
      if (targetLabel && !nodeMap.has(targetId)) nodeMap.set(targetId, targetLabel);
      if (!nodeMap.has(sourceId)) nodeMap.set(sourceId, sourceId);
      if (!nodeMap.has(targetId)) nodeMap.set(targetId, targetId);

      edges.push({
        id: `e-${sourceId}-${targetId}-${edges.length}`,
        source: sourceId,
        target: targetId,
        label: edgeLabel || undefined,
        animated: edgeType.includes("-.") || edgeType.includes("="),
        style: { stroke: "rgba(255,255,255,0.15)", strokeWidth: 1.5 },
        labelStyle: { fill: "rgba(255,255,255,0.5)", fontSize: 10, fontWeight: 500 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "rgba(255,255,255,0.25)", width: 16, height: 16 },
      });
      continue;
    }

    // Standalone node definition: A[Label] or A(Label) or A{Label} or A>Label]
    const nodeDefMatch = line.match(/^(\w+)[\[({\>]([^\])}\]]+)[\])}\]]/);
    if (nodeDefMatch) {
      const id = nodeDefMatch[1];
      const label = nodeDefMatch[2];
      if (!nodeMap.has(id)) nodeMap.set(id, label);
    }
  }

  // Auto-layout: arrange nodes in a grid
  const ids = Array.from(nodeMap.keys());
  const cols = Math.max(3, Math.ceil(Math.sqrt(ids.length)));
  const xGap = 280;
  const yGap = 160;

  const nodes: Node[] = ids.map((id, i) => {
    const label = nodeMap.get(id) || id;
    return {
      id,
      type: "architecture",
      position: { x: (i % cols) * xGap + 40, y: Math.floor(i / cols) * yGap + 40 },
      data: {
        label,
        icon: getNodeIcon(label),
        colors: getNodeColor(label),
      },
    };
  });

  return { nodes, edges };
}

/* ─────────────── Main Component ─────────────── */
type ArchitectureCanvasProps = {
  mermaidCode: string;
  t: (key: string) => string;
  onSync?: (mermaidCode: string) => Promise<void>;
};

function flowToMermaid(nodes: Node[], edges: Edge[]): string {
  const lines = ["flowchart TD"];
  nodes.forEach(n => {
    const safeLabel = (n.data.label as string).replace(/[\[\]]/g, ' ');
    lines.push(`  ${n.id}[${safeLabel}]`);
  });
  edges.forEach(e => {
    const labelPart = e.label ? `|${e.label}|` : '';
    lines.push(`  ${e.source} -->${labelPart} ${e.target}`);
  });
  return lines.join("\n");
}

export function ArchitectureCanvas({ mermaidCode, t, onSync }: ArchitectureCanvasProps) {
  const [viewMode, setViewMode] = useState<"canvas" | "mermaid">("canvas");
  const [fullscreen, setFullscreen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [selectedNodeLabel, setSelectedNodeLabel] = useState<string | null>(null);

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => parseMermaidToFlow(mermaidCode), [mermaidCode]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) =>
      addEdge(
        {
          ...params,
          animated: true,
          style: { stroke: "rgba(255,255,255,0.2)", strokeWidth: 1.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color: "rgba(255,255,255,0.3)", width: 16, height: 16 },
        },
        eds,
      ),
    );
    setIsDirty(true);
  }, [setEdges]);

  const handleSync = async () => {
    if (!onSync) return;
    setIsSyncing(true);
    try {
      const newMermaid = flowToMermaid(nodes, edges);
      await onSync(newMermaid);
      setIsDirty(false);
    } finally {
      setIsSyncing(false);
    }
  };

  if (viewMode === "mermaid") {
    return (
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-white/90">{t("detail.architectureDiagram")}</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode("canvas")}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-white/60 hover:text-white hover:bg-white/[0.06] transition-all"
            >
              <Layers className="h-3 w-3" />
              {t("detail.canvasInteractive")}
            </button>
          </div>
        </div>
        <MermaidViewer code={mermaidCode} />
      </div>
    );
  }

  const containerClass = fullscreen
    ? "fixed inset-0 z-50 bg-[#050505]"
    : "relative w-full rounded-2xl border border-white/5 bg-[#050505] overflow-hidden";

  return (
    <div>
      {!fullscreen && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-medium text-white/90">{t("detail.architectureDiagram")}</h2>
            {isDirty && onSync && (
               <button
                 onClick={handleSync}
                 disabled={isSyncing}
                 className="flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/20 transition-all disabled:opacity-50"
               >
                 <RefreshCw className={`h-3 w-3 ${isSyncing ? "animate-spin" : ""}`} />
                 {isSyncing ? t("detail.syncingArchitecture") : t("detail.syncArchitecture")}
               </button>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode("mermaid")}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-white/60 hover:text-white hover:bg-white/[0.06] transition-all"
            >
              <Code2 className="h-3 w-3" />
              {t("detail.canvasMermaid")}
            </button>
          </div>
        </div>
      )}
      <div className={containerClass} style={fullscreen ? undefined : { height: 520 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodesDelete={() => setIsDirty(true)}
          onEdgesDelete={() => setIsDirty(true)}
          onConnect={onConnect}
          onNodeClick={(_, node) => setSelectedNodeLabel(String(node.data.label || node.id))}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          proOptions={{ hideAttribution: true }}
          style={{ background: "#050505" }}
          defaultEdgeOptions={{
            style: { stroke: "rgba(255,255,255,0.12)", strokeWidth: 1.5 },
            markerEnd: { type: MarkerType.ArrowClosed, color: "rgba(255,255,255,0.2)" },
          }}
        >
          <Background color="rgba(255,255,255,0.03)" gap={24} size={1} />
          <Controls
            showInteractive={false}
            style={{ background: "#111", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12 }}
          />
          <MiniMap
            nodeColor={() => "rgba(255,255,255,0.15)"}
            maskColor="rgba(0,0,0,0.7)"
            style={{ background: "#0a0a0a", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12 }}
          />
          <Panel position="top-right" className="flex gap-2">
            <button
              onClick={() => setFullscreen((f) => !f)}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-black/80 backdrop-blur-sm px-3 py-1.5 text-xs font-medium text-white/60 hover:text-white hover:bg-white/[0.06] transition-all"
            >
              {fullscreen ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
              {fullscreen ? t("detail.canvasExit") : t("detail.canvasFullscreen")}
            </button>
            {fullscreen && (
              <button
                onClick={() => setViewMode("mermaid")}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-black/80 backdrop-blur-sm px-3 py-1.5 text-xs font-medium text-white/60 hover:text-white hover:bg-white/[0.06] transition-all"
              >
                <Eye className="h-3 w-3" />
                {t("detail.showRawMermaid")}
              </button>
            )}
          </Panel>
          {selectedNodeLabel ? (
            <Panel position="bottom-left" className="rounded-lg border border-white/10 bg-black/70 px-3 py-2 text-xs text-white/70">
              {t("detail.selectedNode")}: <span className="text-white">{selectedNodeLabel}</span>
            </Panel>
          ) : null}
        </ReactFlow>
      </div>
    </div>
  );
}
