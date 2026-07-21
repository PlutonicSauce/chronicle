-- Apply with the CockroachDB SQL client, not the Cloud web SQL Shell:
-- cockroach sql --url "$DATABASE_URL" --file=infra/vector-index.sql
-- Vector indexing is enabled by default on current CockroachDB Cloud clusters.
CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx
  ON memories (project_id, embedding vector_cosine_ops);
