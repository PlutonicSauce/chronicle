"""CockroachDB implementation of Chronicle's memory repository."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.schemas import MemoryCreate
from app.services.embedding import Embedder
from app.settings import Settings

COCKROACH_CLOUD_CA = Path(__file__).resolve().parents[1] / "certs" / "isrgrootx1.pem"


def _vector_literal(values: Iterable[float]) -> str:
    return "[" + ",".join(f"{value:.9f}" for value in values) + "]"


def _keyword_score(row: dict, query: str) -> float:
    """Portable keyword scoring for Cloud-compatible memory retrieval."""
    terms = [term for term in query.lower().split() if term]
    if not terms:
        return 0.0
    haystack = " ".join(
        [row["title"], row["summary"], row["repository"], *list(row.get("tags") or [])]
    ).lower()
    return min(1.0, sum(term in haystack for term in terms) / len(terms))


class CockroachMemoryStore:
    """Repository that keeps records, vectors, and relationship edges transactional."""

    def __init__(self, settings: Settings, embedder: Embedder):
        if not settings.database_url:
            raise ValueError("DATABASE_URL is required for CockroachMemoryStore")
        self.settings = settings
        self.embedder = embedder
        self._project_id: str | None = None

    def _connection(self):
        # CockroachDB Basic uses a Let's Encrypt chain. Bundle the trusted root so
        # Lambda can retain TLS hostname and certificate verification.
        return psycopg.connect(
            self.settings.database_url,
            row_factory=dict_row,
            sslrootcert=str(COCKROACH_CLOUD_CA),
        )

    def _project(self) -> str:
        if self._project_id:
            return self._project_id
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO projects (slug, name, repository)
                VALUES (%s, %s, %s)
                ON CONFLICT (slug) DO UPDATE SET name = excluded.name
                RETURNING id
                """,
                (self.settings.project_slug, self.settings.project_name, self.settings.project_repository),
            )
            row = cursor.fetchone()
        self._project_id = str(row["id"])
        return self._project_id

    @staticmethod
    def _public(row: dict, score: float | None = None) -> dict:
        data = {
            "id": str(row["id"]),
            "title": row["title"],
            "summary": row["summary"],
            "source_kind": row["source_kind"],
            "source_url": row.get("source_url"),
            "occurred_at": row["occurred_at"],
            "created_at": row["created_at"],
            "tags": list(row.get("tags") or []),
            "confidence": float(row["confidence"]),
            "importance": float(row["importance"]),
            "created_by": row["created_by"],
            "repository": row["repository"],
            "commit_hash": row.get("commit_hash"),
            "branch": row.get("branch"),
            "metadata": row.get("metadata") or {},
        }
        if score is not None:
            data["score"] = round(max(0.0, min(1.0, score)), 3)
        return data

    def search(self, query: str, mode: str, limit: int = 12) -> list[dict]:
        project_id = self._project()
        if not query.strip():
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM memories
                    WHERE project_id = %s
                    ORDER BY occurred_at DESC
                    LIMIT %s
                    """,
                    (project_id, limit),
                )
                return [self._public(row) for row in cursor.fetchall()]

        if mode == "keyword":
            pattern = f"%{query}%"
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM memories
                    WHERE project_id = %s
                      AND (title ILIKE %s OR summary ILIKE %s OR repository ILIKE %s)
                    ORDER BY importance DESC, occurred_at DESC
                    LIMIT %s
                    """,
                    (project_id, pattern, pattern, pattern, limit),
                )
                return [self._public(row, _keyword_score(row, query)) for row in cursor.fetchall()]

        vector = _vector_literal(self.embedder.embed(query))
        candidate_limit = max(limit * 5, 40) if mode == "hybrid" else limit
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                    """
                    SELECT *,
                       1 - (embedding <=> %s::VECTOR) AS semantic_score
                    FROM memories
                    WHERE project_id = %s
                    ORDER BY embedding <=> %s::VECTOR
                    LIMIT %s
                    """,
                (vector, project_id, vector, candidate_limit),
            )
            rows = cursor.fetchall()

        if mode == "semantic":
            return [self._public(row, float(row["semantic_score"])) for row in rows]

        ranked = sorted(
            (
                (
                    0.68 * float(row["semantic_score"])
                    + 0.32 * _keyword_score(row, query),
                    row,
                )
                for row in rows
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        return [self._public(row, score) for score, row in ranked[:limit]]

    def get_memory(self, memory_id: str) -> dict | None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM memories WHERE id = %s AND project_id = %s",
                (memory_id, self._project()),
            )
            row = cursor.fetchone()
        return self._public(row) if row else None

    def detail(self, memory_id: str) -> dict | None:
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT from_memory_id, to_memory_id, relationship_kind, confidence
                FROM memory_relationships
                WHERE from_memory_id = %s OR to_memory_id = %s
                """,
                (memory_id, memory_id),
            )
            relationships = [
                {
                    **row,
                    "from_memory_id": str(row["from_memory_id"]),
                    "to_memory_id": str(row["to_memory_id"]),
                    "confidence": float(row["confidence"]),
                }
                for row in cursor.fetchall()
            ]
        related_ids = {
            edge["to_memory_id"] if edge["from_memory_id"] == memory_id else edge["from_memory_id"]
            for edge in relationships
        }
        related = [candidate for candidate_id in related_ids if (candidate := self.get_memory(candidate_id))]
        return {"memory": memory, "relationships": relationships, "related_memories": related}

    def graph(self, memory_id: str) -> dict | None:
        detail = self.detail(memory_id)
        if not detail:
            return None
        memories = [detail["memory"], *detail["related_memories"]]
        return {
            "focus_memory_id": memory_id,
            "nodes": [
                {
                    "id": memory["id"],
                    "label": memory["title"],
                    "kind": memory["source_kind"],
                    "importance": memory["importance"],
                    "is_focus": memory["id"] == memory_id,
                }
                for memory in memories
            ],
            "edges": detail["relationships"],
        }

    def timeline(self, limit: int = 30) -> list[dict]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM memories
                WHERE project_id = %s
                ORDER BY occurred_at DESC
                LIMIT %s
                """,
                (self._project(), limit),
            )
            rows = cursor.fetchall()
        groups: dict[str, list[dict]] = {}
        for row in rows:
            memory = self._public(row)
            date = memory["occurred_at"].date().isoformat()
            groups.setdefault(date, []).append(memory)
        return [{"date": date, "memories": memories} for date, memories in groups.items()]

    def dashboard(self) -> dict:
        project_id = self._project()
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*) AS total_memories,
                       count(DISTINCT created_by) AS active_agents,
                       coalesce(avg((confidence >= 0.9)::INT), 0) AS high_confidence_ratio
                FROM memories WHERE project_id = %s
                """,
                (project_id,),
            )
            stats = cursor.fetchone()
            cursor.execute(
                """
                SELECT count(*) AS relationships FROM memory_relationships r
                JOIN memories m ON m.id = r.from_memory_id
                WHERE m.project_id = %s
                """,
                (project_id,),
            )
            relationship_count = cursor.fetchone()["relationships"]
            cursor.execute(
                """
                SELECT * FROM memories WHERE project_id = %s
                ORDER BY importance DESC, occurred_at DESC LIMIT 3
                """,
                (project_id,),
            )
            featured = [self._public(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT * FROM memories WHERE project_id = %s
                ORDER BY occurred_at DESC LIMIT 5
                """,
                (project_id,),
            )
            recent = [self._public(row) for row in cursor.fetchall()]
        return {
            "project_name": self.settings.project_name,
            "project_slug": self.settings.project_slug,
            "repository": self.settings.project_repository,
            "stats": {
                "total_memories": int(stats["total_memories"]),
                "relationships": int(relationship_count),
                "high_confidence_ratio": float(stats["high_confidence_ratio"]),
                "active_agents": int(stats["active_agents"]),
            },
            "recent_activity": [
                {
                    "id": f"captured-{memory['id']}",
                    "action": "captured memory",
                    "actor": memory["created_by"],
                    "occurred_at": memory["occurred_at"],
                    "memory_id": memory["id"],
                    "memory_title": memory["title"],
                }
                for memory in recent
            ],
            "featured_memories": featured,
            "mode": "live",
        }

    def create_memory(self, payload: MemoryCreate) -> dict:
        vector = _vector_literal(self.embedder.embed(f"{payload.title}\n{payload.summary}\n{' '.join(payload.tags)}"))
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO memories (
                    project_id, title, summary, source_kind, source_url, occurred_at, tags,
                    confidence, importance, created_by, repository, commit_hash, branch, metadata, embedding
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::VECTOR
                ) RETURNING *
                """,
                (
                    self._project(),
                    payload.title,
                    payload.summary,
                    payload.source_kind,
                    payload.source_url,
                    payload.occurred_at,
                    payload.tags,
                    payload.confidence,
                    payload.importance,
                    payload.created_by,
                    payload.repository,
                    payload.commit_hash,
                    payload.branch,
                    Jsonb(payload.metadata),
                    vector,
                ),
            )
            row = cursor.fetchone()
        return self._public(row)

    def record_access(self, memory_id: str, actor: str, action: str, query: str | None = None) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO memory_access_log (memory_id, actor, action, query_text, occurred_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (memory_id, actor, action, query, datetime.now(UTC)),
            )

    def export(self) -> list[dict]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM memories WHERE project_id = %s ORDER BY occurred_at DESC",
                (self._project(),),
            )
            return [self._public(row) for row in cursor.fetchall()]
