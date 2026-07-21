-- Chronicle's permanent engineering memory store.
-- Run on a CockroachDB Cloud cluster before the API starts.
-- Apply vector-index.sql separately with the CockroachDB SQL client. The Cloud
-- web SQL Shell currently uses a schema-change route that cannot build vector
-- indexes.

CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug STRING NOT NULL UNIQUE,
  name STRING NOT NULL,
  repository STRING NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id),
  title STRING NOT NULL,
  summary STRING NOT NULL,
  source_kind STRING NOT NULL,
  source_url STRING,
  occurred_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  tags STRING[] NOT NULL DEFAULT ARRAY[]:::STRING[],
  confidence FLOAT8 NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  importance FLOAT8 NOT NULL CHECK (importance >= 0 AND importance <= 1),
  created_by STRING NOT NULL,
  repository STRING NOT NULL,
  commit_hash STRING,
  branch STRING,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  embedding VECTOR(512) NOT NULL
);

CREATE INDEX IF NOT EXISTS memories_project_time_idx
  ON memories (project_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS memory_relationships (
  from_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  to_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  relationship_kind STRING NOT NULL,
  confidence FLOAT8 NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (from_memory_id, to_memory_id, relationship_kind),
  CHECK (from_memory_id != to_memory_id)
);

CREATE INDEX IF NOT EXISTS memory_relationships_target_idx
  ON memory_relationships (to_memory_id);

CREATE TABLE IF NOT EXISTS memory_access_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  memory_id UUID NOT NULL REFERENCES memories(id),
  actor STRING NOT NULL,
  action STRING NOT NULL,
  query_text STRING,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS memory_access_log_memory_time_idx
  ON memory_access_log (memory_id, occurred_at DESC);
