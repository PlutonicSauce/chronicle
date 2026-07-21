import type { Graph } from "../lib/types";

const positions = [
  { x: 50, y: 50 },
  { x: 81, y: 23 },
  { x: 18, y: 76 },
  { x: 80, y: 76 },
  { x: 18, y: 23 },
];

export function MemoryGraph({ graph, onSelect }: { graph: Graph; onSelect?: (id: string) => void }) {
  const byId = new Map(graph.nodes.map((node, index) => [node.id, { ...node, ...positions[index] }]));
  return (
    <div className="memory-graph" aria-label="Relationship graph">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <pattern id="graph-grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(152,164,196,.12)" strokeWidth=".35" />
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#graph-grid)" />
        {graph.edges.map((edge) => {
          const source = byId.get(edge.from_memory_id);
          const target = byId.get(edge.to_memory_id);
          if (!source || !target) return null;
          return (
            <line
              key={`${edge.from_memory_id}-${edge.to_memory_id}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="rgba(157, 173, 255, .5)"
              strokeDasharray="2 1.5"
              strokeWidth=".55"
            />
          );
        })}
      </svg>
      {Array.from(byId.values()).map((node) => (
        <button
          className={`graph-node ${node.is_focus ? "focus" : ""}`}
          key={node.id}
          type="button"
          style={{ left: `${node.x}%`, top: `${node.y}%` }}
          onClick={() => onSelect?.(node.id)}
          title={node.label}
        >
          <span />
          <small>{node.is_focus ? "focus" : node.kind}</small>
        </button>
      ))}
      <div className="graph-legend"><i /> Relationship edge · confidence weighted</div>
    </div>
  );
}
