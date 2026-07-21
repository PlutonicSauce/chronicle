import type { Dashboard, Graph, Memory, MemoryDetail, SearchResponse } from "./types";

const timestamp = (day: string, time: string) => `2026-07-${day}T${time}:00Z`;

export const demoMemories: Memory[] = [
  {
    id: "019f827f-0001-7000-8000-000000000001",
    title: "Moved session validation to the edge gateway",
    summary:
      "Authentication changed because SSR requests were refreshing tokens independently and creating rotating-token races. The edge gateway now validates the signed session once and forwards a short-lived identity header to Atlas services.",
    source_kind: "architecture-decision",
    occurred_at: timestamp("16", "14:22"),
    created_at: timestamp("16", "14:22"),
    tags: ["authentication", "edge", "sessions"],
    confidence: 0.97,
    importance: 0.94,
    created_by: "claude-code",
    repository: "acme/atlas",
    commit_hash: "a91c3fe",
    branch: "main",
    metadata: { decision: "ADR-042", status: "accepted" },
    score: 0.94,
  },
  {
    id: "019f827f-0002-7000-8000-000000000002",
    title: "Fixed OAuth callback loop for SAML tenants",
    summary:
      "The login callback loop was caused by a missing tenant origin in the session claim. Adding the origin before exchanging the authorization code fixed SAML sign-in without weakening CSRF checks.",
    source_kind: "bug-fix",
    occurred_at: timestamp("17", "09:08"),
    created_at: timestamp("17", "09:08"),
    tags: ["authentication", "oauth", "saml"],
    confidence: 0.96,
    importance: 0.9,
    created_by: "cursor-agent",
    repository: "acme/atlas",
    commit_hash: "f42ac09",
    branch: "main",
    metadata: {},
    score: 0.89,
  },
  {
    id: "019f827f-0003-7000-8000-000000000003",
    title: "Abandoned shared refresh-token cache",
    summary:
      "We tested a shared Redis cache for refresh token coordination. It reduced races but introduced a regional dependency and inconsistent logout propagation, so the approach was rejected in favor of edge validation.",
    source_kind: "failed-experiment",
    occurred_at: timestamp("15", "16:41"),
    created_at: timestamp("15", "16:41"),
    tags: ["authentication", "redis", "rejected"],
    confidence: 0.92,
    importance: 0.83,
    created_by: "claude-code",
    repository: "acme/atlas",
    commit_hash: "c631e0a",
    branch: "main",
    metadata: {},
    score: 0.78,
  },
  {
    id: "019f827f-0005-7000-8000-000000000005",
    title: "Incident: release queue backed up in us-east-1",
    summary:
      "A deploy worker retry storm delayed 38 releases for 19 minutes. We added a per-repository retry budget and backfilled audits.",
    source_kind: "incident",
    occurred_at: timestamp("18", "18:12"),
    created_at: timestamp("18", "18:12"),
    tags: ["incident", "deployments", "queue"],
    confidence: 0.95,
    importance: 0.97,
    created_by: "incident-bot",
    repository: "acme/atlas",
    commit_hash: "e90b18f",
    branch: "main",
    metadata: { severity: "SEV-2" },
    score: 0.66,
  },
  {
    id: "019f827f-0006-7000-8000-000000000006",
    title: "Chose an append-only deployment audit trail",
    summary:
      "Deployment state is immutable and represented as ordered events instead of an overwritten status row. This makes retries, rollbacks, and agent reasoning independently reconstructable.",
    source_kind: "architecture-decision",
    occurred_at: timestamp("12", "10:02"),
    created_at: timestamp("12", "10:02"),
    tags: ["deployments", "audit", "event-sourcing"],
    confidence: 0.94,
    importance: 0.93,
    created_by: "claude-code",
    repository: "acme/atlas",
    commit_hash: "98d7bb1",
    branch: "main",
    metadata: {},
    score: 0.61,
  },
  {
    id: "019f827f-0007-7000-8000-000000000007",
    title: "Optimized project overview query with a covering index",
    summary:
      "A covering index on project_id and occurred_at removed an index join and returned the project overview to p95 74ms.",
    source_kind: "performance-fix",
    occurred_at: timestamp("14", "13:18"),
    created_at: timestamp("14", "13:18"),
    tags: ["performance", "cockroachdb", "indexing"],
    confidence: 0.93,
    importance: 0.86,
    created_by: "cursor-agent",
    repository: "acme/atlas",
    commit_hash: "a3102d5",
    branch: "main",
    metadata: {},
    score: 0.54,
  },
];

export const demoRelationships = [
  {
    from_memory_id: demoMemories[2].id,
    to_memory_id: demoMemories[0].id,
    relationship_kind: "led_to",
    confidence: 0.94,
  },
  {
    from_memory_id: demoMemories[0].id,
    to_memory_id: demoMemories[1].id,
    relationship_kind: "enabled",
    confidence: 0.88,
  },
];

export const demoDashboard: Dashboard = {
  project_name: "Atlas",
  project_slug: "atlas",
  repository: "acme/atlas",
  stats: { total_memories: 10, relationships: 6, high_confidence_ratio: 0.96, active_agents: 4 },
  recent_activity: demoMemories.slice(0, 5).map((memory) => ({
    id: `activity-${memory.id}`,
    action: "captured memory",
    actor: memory.created_by,
    occurred_at: memory.occurred_at,
    memory_id: memory.id,
    memory_title: memory.title,
  })),
  featured_memories: [demoMemories[3], demoMemories[0], demoMemories[4]],
  mode: "demo",
};

export const demoDetail: MemoryDetail = {
  memory: demoMemories[0],
  relationships: demoRelationships,
  related_memories: [demoMemories[1], demoMemories[2]],
};

export const demoGraph: Graph = {
  focus_memory_id: demoMemories[0].id,
  nodes: [
    { id: demoMemories[0].id, label: demoMemories[0].title, kind: "decision", importance: 0.94, is_focus: true },
    { id: demoMemories[1].id, label: demoMemories[1].title, kind: "fix", importance: 0.9, is_focus: false },
    { id: demoMemories[2].id, label: demoMemories[2].title, kind: "experiment", importance: 0.83, is_focus: false },
  ],
  edges: demoRelationships,
};

export const demoSearch: SearchResponse = {
  query: "Why did authentication change?",
  mode: "hybrid",
  results: demoMemories,
  total: demoMemories.length,
  retrieval_note: "Combines semantic similarity with keyword relevance.",
};
