import { ArrowUpRight, GitCommitHorizontal, Sparkles } from "lucide-react";

import type { Memory } from "../lib/types";

const kindLabel: Record<string, string> = {
  "architecture-decision": "decision",
  "failed-experiment": "learned",
  "performance-fix": "optimization",
  "bug-fix": "fix",
  "api-change": "api change",
};

function dateLabel(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(new Date(value));
}

export function MemoryRow({
  memory,
  selected,
  onSelect,
}: {
  memory: Memory;
  selected: boolean;
  onSelect: (memory: Memory) => void;
}) {
  return (
    <button
      className={`memory-row ${selected ? "selected" : ""}`}
      type="button"
      onClick={() => onSelect(memory)}
    >
      <span className="memory-date">{dateLabel(memory.occurred_at)}</span>
      <span className="memory-rail" aria-hidden="true">
        <span />
      </span>
      <span className="memory-copy">
        <span className="memory-eyebrow">
          <span className="kind-pill">{kindLabel[memory.source_kind] ?? memory.source_kind}</span>
          <span>{memory.created_by}</span>
          {memory.score ? <span className="score"><Sparkles size={11} /> {Math.round(memory.score * 100)}%</span> : null}
        </span>
        <span className="memory-title">{memory.title}</span>
        <span className="memory-summary">{memory.summary}</span>
        <span className="memory-meta">
          {memory.tags.slice(0, 3).map((tag) => (
            <span key={tag}>#{tag}</span>
          ))}
          {memory.commit_hash ? (
            <span className="commit"><GitCommitHorizontal size={13} />{memory.commit_hash}</span>
          ) : null}
        </span>
      </span>
      <ArrowUpRight className="memory-arrow" size={17} strokeWidth={1.5} />
    </button>
  );
}
