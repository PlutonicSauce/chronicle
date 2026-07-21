export type SearchMode = "semantic" | "hybrid" | "keyword";

export type Memory = {
  id: string;
  title: string;
  summary: string;
  source_kind: string;
  source_url?: string | null;
  occurred_at: string;
  created_at: string;
  tags: string[];
  confidence: number;
  importance: number;
  created_by: string;
  repository: string;
  commit_hash?: string | null;
  branch?: string | null;
  metadata: Record<string, unknown>;
  score?: number | null;
};

export type Relationship = {
  from_memory_id: string;
  to_memory_id: string;
  relationship_kind: string;
  confidence: number;
};

export type MemoryDetail = {
  memory: Memory;
  relationships: Relationship[];
  related_memories: Memory[];
};

export type Graph = {
  focus_memory_id: string;
  nodes: Array<{
    id: string;
    label: string;
    kind: string;
    importance: number;
    is_focus: boolean;
  }>;
  edges: Relationship[];
};

export type Dashboard = {
  project_name: string;
  project_slug: string;
  repository: string;
  stats: {
    total_memories: number;
    relationships: number;
    high_confidence_ratio: number;
    active_agents: number;
  };
  recent_activity: Array<{
    id: string;
    action: string;
    actor: string;
    occurred_at: string;
    memory_id: string;
    memory_title: string;
  }>;
  featured_memories: Memory[];
  mode: "demo" | "live";
};

export type SearchResponse = {
  query: string;
  mode: SearchMode;
  results: Memory[];
  total: number;
  retrieval_note: string;
};
