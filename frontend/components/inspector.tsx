import { Braces, CircleCheck, GitBranch, Link2, ShieldCheck } from "lucide-react";

import type { MemoryDetail } from "../lib/types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function Inspector({ detail }: { detail: MemoryDetail }) {
  const { memory, relationships, related_memories: related } = detail;
  return (
    <section className="inspector" aria-label="Memory inspector">
      <div className="panel-heading">
        <div>
          <span className="overline">Memory inspector</span>
          <h2>Context, not chat history.</h2>
        </div>
        <span className="confidence"><ShieldCheck size={14} /> {Math.round(memory.confidence * 100)}%</span>
      </div>
      <article className="inspector-memory">
        <span className="kind-pill">{memory.source_kind.replaceAll("-", " ")}</span>
        <h3>{memory.title}</h3>
        <p>{memory.summary}</p>
        <dl className="memory-facts">
          <div><dt>Captured</dt><dd>{formatDate(memory.occurred_at)}</dd></div>
          <div><dt>Agent</dt><dd>{memory.created_by}</dd></div>
          <div><dt>Branch</dt><dd><GitBranch size={13} />{memory.branch ?? "—"}</dd></div>
          <div><dt>Evidence</dt><dd><Braces size={13} />{memory.commit_hash ?? "context note"}</dd></div>
        </dl>
      </article>
      <div className="inspector-section">
        <div className="section-label"><Link2 size={14} /> Connected memory <span>{relationships.length}</span></div>
        {related.length ? related.map((item) => {
          const relationship = relationships.find(
            (edge) =>
              (edge.from_memory_id === memory.id && edge.to_memory_id === item.id) ||
              (edge.to_memory_id === memory.id && edge.from_memory_id === item.id),
          );
          return (
          <div className="related-memory" key={item.id}>
            <span>{relationship?.relationship_kind.replaceAll("_", " ") ?? "related"}</span>
            <strong>{item.title}</strong>
          </div>
          );
        }) : <p className="quiet">No direct edges yet. Chronicle will surface causal links as activity accumulates.</p>}
      </div>
      <div className="inspector-section reasoning">
        <div className="section-label"><CircleCheck size={14} /> Reasoning trail</div>
        <ol>
          <li><span>01</span>Extracted a durable implementation rationale.</li>
          <li><span>02</span>Embedded alongside prior authentication work.</li>
          <li><span>03</span>Linked to the experiment it replaced.</li>
        </ol>
      </div>
    </section>
  );
}
