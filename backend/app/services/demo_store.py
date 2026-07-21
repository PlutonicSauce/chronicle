"""Seeded, deterministic local store that makes the submission runnable without cloud setup."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.schemas import MemoryCreate
from app.services.embedding import deterministic_embedding
from app.settings import Settings


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def _record(
    record_id: str,
    title: str,
    summary: str,
    source_kind: str,
    occurred_at: str,
    tags: list[str],
    confidence: float,
    importance: float,
    created_by: str,
    commit_hash: str | None = None,
    branch: str | None = "main",
    metadata: dict | None = None,
) -> dict:
    occurred = _timestamp(occurred_at)
    return {
        "id": record_id,
        "title": title,
        "summary": summary,
        "source_kind": source_kind,
        "source_url": None,
        "occurred_at": occurred,
        "created_at": occurred,
        "tags": tags,
        "confidence": confidence,
        "importance": importance,
        "created_by": created_by,
        "repository": "acme/atlas",
        "commit_hash": commit_hash,
        "branch": branch,
        "metadata": metadata or {},
        "embedding": deterministic_embedding(f"{title} {summary} {' '.join(tags)}"),
    }


_SEED_MEMORIES = [
    _record(
        "019f827f-0001-7000-8000-000000000001",
        "Moved session validation to the edge gateway",
        "Authentication changed because SSR requests were refreshing tokens independently and creating "
        "rotating-token races. The edge gateway now validates the signed session once and forwards a "
        "short-lived identity header to Atlas services.",
        "architecture-decision",
        "2026-07-16T14:22:00",
        ["authentication", "edge", "sessions"],
        0.97,
        0.94,
        "claude-code",
        "a91c3fe",
        metadata={"decision": "ADR-042", "status": "accepted"},
    ),
    _record(
        "019f827f-0002-7000-8000-000000000002",
        "Fixed OAuth callback loop for SAML tenants",
        "The login callback loop was caused by a missing tenant origin in the session claim. Adding the "
        "origin before exchanging the authorization code fixed SAML sign-in without weakening CSRF checks.",
        "bug-fix",
        "2026-07-17T09:08:00",
        ["authentication", "oauth", "saml", "incident"],
        0.96,
        0.9,
        "cursor-agent",
        "f42ac09",
    ),
    _record(
        "019f827f-0003-7000-8000-000000000003",
        "Abandoned shared refresh-token cache",
        "We tested a shared Redis cache for refresh token coordination. It reduced races but introduced a "
        "regional dependency and inconsistent logout propagation, so the approach was rejected in favor of edge validation.",
        "failed-experiment",
        "2026-07-15T16:41:00",
        ["authentication", "redis", "rejected"],
        0.92,
        0.83,
        "claude-code",
        "c631e0a",
    ),
    _record(
        "019f827f-0004-7000-8000-000000000004",
        "Added idempotency keys to webhook ingestion",
        "Duplicate GitHub delivery retries created two deployment records when a worker restarted between write "
        "and acknowledgement. Deliveries now use a repository-scoped idempotency key and transactional insert.",
        "bug-fix",
        "2026-07-18T11:36:00",
        ["webhooks", "idempotency", "cockroachdb"],
        0.98,
        0.91,
        "chronicle-agent",
        "d48ee67",
    ),
    _record(
        "019f827f-0005-7000-8000-000000000005",
        "Incident: release queue backed up in us-east-1",
        "A deploy worker retry storm delayed 38 releases for 19 minutes. The circuit breaker tripped only after "
        "the queue exceeded its default threshold. We raised visibility, added a per-repository retry budget, and backfilled audits.",
        "incident",
        "2026-07-18T18:12:00",
        ["incident", "deployments", "queue", "aws"],
        0.95,
        0.97,
        "incident-bot",
        "e90b18f",
        metadata={"severity": "SEV-2", "duration_minutes": 19},
    ),
    _record(
        "019f827f-0006-7000-8000-000000000006",
        "Chose an append-only deployment audit trail",
        "Deployment state is immutable and represented as ordered events instead of an overwritten status row. "
        "This makes retries, rollbacks, and agent reasoning independently reconstructable.",
        "architecture-decision",
        "2026-07-12T10:02:00",
        ["deployments", "audit", "event-sourcing"],
        0.94,
        0.93,
        "claude-code",
        "98d7bb1",
    ),
    _record(
        "019f827f-0007-7000-8000-000000000007",
        "Optimized project overview query with a covering index",
        "The project overview exceeded its 300ms budget after repositories crossed 10k deployments. A covering "
        "index on project_id and occurred_at removed an index join and returned the page to p95 74ms.",
        "performance-fix",
        "2026-07-14T13:18:00",
        ["performance", "cockroachdb", "indexing"],
        0.93,
        0.86,
        "cursor-agent",
        "a3102d5",
    ),
    _record(
        "019f827f-0008-7000-8000-000000000008",
        "Introduced repository-aware memory isolation",
        "Memories may share patterns across the company, but retrieval defaults to the current repository. Cross-repo "
        "links are explicit relationships so a coding agent cannot accidentally blend unrelated service history.",
        "architecture-decision",
        "2026-07-10T15:44:00",
        ["memory", "security", "retrieval"],
        0.98,
        0.95,
        "chronicle-agent",
        "3d83cc2",
    ),
    _record(
        "019f827f-0009-7000-8000-000000000009",
        "Migration: normalized service ownership",
        "Ownership moved from a JSON release payload to a relational service_owners table. This lets incident "
        "routing and deployment approvals remain consistent with the latest ownership graph.",
        "migration",
        "2026-07-11T08:23:00",
        ["migration", "ownership", "schema"],
        0.94,
        0.8,
        "claude-code",
        "0dd41aa",
    ),
    _record(
        "019f827f-0010-7000-8000-000000000010",
        "Deprecated the v1 deploy status endpoint",
        "The v1 endpoint returned a mutable current status with no audit context. Consumers have until August 31 to "
        "move to the event timeline endpoint, which includes state transitions and rollback reasons.",
        "api-change",
        "2026-07-19T12:06:00",
        ["api", "deployments", "deprecation"],
        0.96,
        0.88,
        "cursor-agent",
        "be91f28",
    ),
]

_SEED_RELATIONSHIPS = [
    {
        "from_memory_id": "019f827f-0003-7000-8000-000000000003",
        "to_memory_id": "019f827f-0001-7000-8000-000000000001",
        "relationship_kind": "led_to",
        "confidence": 0.94,
    },
    {
        "from_memory_id": "019f827f-0001-7000-8000-000000000001",
        "to_memory_id": "019f827f-0002-7000-8000-000000000002",
        "relationship_kind": "enabled",
        "confidence": 0.88,
    },
    {
        "from_memory_id": "019f827f-0006-7000-8000-000000000006",
        "to_memory_id": "019f827f-0005-7000-8000-000000000005",
        "relationship_kind": "explains",
        "confidence": 0.86,
    },
    {
        "from_memory_id": "019f827f-0004-7000-8000-000000000004",
        "to_memory_id": "019f827f-0005-7000-8000-000000000005",
        "relationship_kind": "prevented_repeat",
        "confidence": 0.78,
    },
    {
        "from_memory_id": "019f827f-0006-7000-8000-000000000006",
        "to_memory_id": "019f827f-0010-7000-8000-000000000010",
        "relationship_kind": "supersedes",
        "confidence": 0.9,
    },
    {
        "from_memory_id": "019f827f-0008-7000-8000-000000000008",
        "to_memory_id": "019f827f-0001-7000-8000-000000000001",
        "relationship_kind": "scopes",
        "confidence": 0.97,
    },
]


class DemoMemoryStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.memories = {memory["id"]: memory for memory in _SEED_MEMORIES}
        self.relationships = list(_SEED_RELATIONSHIPS)
        self.access_log: list[dict] = []

    @staticmethod
    def _public(memory: dict, score: float | None = None) -> dict:
        result = {key: value for key, value in memory.items() if key != "embedding"}
        if score is not None:
            result["score"] = round(score, 3)
        return result

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=True))

    @staticmethod
    def _keywords(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9][a-z0-9_-]{1,}", text.lower()))

    def _keyword_score(self, memory: dict, query_tokens: set[str]) -> float:
        if not query_tokens:
            return 0.0
        title = self._keywords(memory["title"])
        body = self._keywords(memory["summary"])
        tags = set(memory["tags"])
        weighted_hits = 3 * len(query_tokens & title) + len(query_tokens & body) + 2 * len(query_tokens & tags)
        return weighted_hits / (len(query_tokens) * 3)

    def search(self, query: str, mode: str, limit: int = 12) -> list[dict]:
        if not query.strip():
            ordered = sorted(self.memories.values(), key=lambda item: item["occurred_at"], reverse=True)
            return [self._public(memory) for memory in ordered[:limit]]

        query_vector = deterministic_embedding(query)
        query_tokens = self._keywords(query)
        ranked: list[tuple[float, dict]] = []
        for memory in self.memories.values():
            semantic = max(0.0, self._cosine(query_vector, memory["embedding"]))
            keyword = min(1.0, self._keyword_score(memory, query_tokens))
            if mode == "semantic":
                score = semantic
            elif mode == "keyword":
                score = keyword
            else:
                score = 0.68 * semantic + 0.32 * keyword
            ranked.append((score, memory))

        ranked.sort(key=lambda item: (item[0], item[1]["importance"], item[1]["occurred_at"]), reverse=True)
        return [self._public(memory, score) for score, memory in ranked[:limit] if score > 0 or mode != "keyword"]

    def get_memory(self, memory_id: str) -> dict | None:
        memory = self.memories.get(memory_id)
        return self._public(memory) if memory else None

    def detail(self, memory_id: str) -> dict | None:
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        relationships = [
            edge
            for edge in self.relationships
            if edge["from_memory_id"] == memory_id or edge["to_memory_id"] == memory_id
        ]
        related_ids = {
            edge["to_memory_id"] if edge["from_memory_id"] == memory_id else edge["from_memory_id"]
            for edge in relationships
        }
        related = [self._public(self.memories[related_id]) for related_id in related_ids]
        return {"memory": memory, "relationships": relationships, "related_memories": related}

    def graph(self, memory_id: str) -> dict | None:
        detail = self.detail(memory_id)
        if not detail:
            return None
        nodes = [
            {
                "id": detail["memory"]["id"],
                "label": detail["memory"]["title"],
                "kind": detail["memory"]["source_kind"],
                "importance": detail["memory"]["importance"],
                "is_focus": True,
            }
        ]
        nodes.extend(
            {
                "id": memory["id"],
                "label": memory["title"],
                "kind": memory["source_kind"],
                "importance": memory["importance"],
                "is_focus": False,
            }
            for memory in detail["related_memories"]
        )
        return {"focus_memory_id": memory_id, "nodes": nodes, "edges": detail["relationships"]}

    def timeline(self, limit: int = 30) -> list[dict]:
        groups: dict[str, list[dict]] = {}
        ordered = sorted(self.memories.values(), key=lambda item: item["occurred_at"], reverse=True)[:limit]
        for memory in ordered:
            key = memory["occurred_at"].date().isoformat()
            groups.setdefault(key, []).append(self._public(memory))
        return [{"date": date, "memories": memories} for date, memories in groups.items()]

    def dashboard(self) -> dict:
        memories = list(self.memories.values())
        created_by = {memory["created_by"] for memory in memories}
        featured = sorted(memories, key=lambda item: item["importance"], reverse=True)[:3]
        latest = sorted(memories, key=lambda item: item["occurred_at"], reverse=True)[:5]
        return {
            "project_name": self.settings.project_name,
            "project_slug": self.settings.project_slug,
            "repository": self.settings.project_repository,
            "stats": {
                "total_memories": len(memories),
                "relationships": len(self.relationships),
                "high_confidence_ratio": round(
                    sum(memory["confidence"] >= 0.9 for memory in memories) / len(memories), 2
                ),
                "active_agents": len(created_by),
            },
            "recent_activity": [
                {
                    "id": f"activity-{memory['id']}",
                    "action": "captured memory",
                    "actor": memory["created_by"],
                    "occurred_at": memory["occurred_at"],
                    "memory_id": memory["id"],
                    "memory_title": memory["title"],
                }
                for memory in latest
            ],
            "featured_memories": [self._public(memory) for memory in featured],
            "mode": "demo",
        }

    def create_memory(self, payload: MemoryCreate) -> dict:
        memory_id = str(uuid4())
        memory = _record(
            memory_id,
            payload.title,
            payload.summary,
            payload.source_kind,
            payload.occurred_at.isoformat(),
            payload.tags,
            payload.confidence,
            payload.importance,
            payload.created_by,
            payload.commit_hash,
            payload.branch,
            payload.metadata,
        )
        memory["source_url"] = payload.source_url
        memory["repository"] = payload.repository
        self.memories[memory_id] = memory
        return self._public(memory)

    def record_access(self, memory_id: str, actor: str, action: str, query: str | None = None) -> None:
        memory = self.memories.get(memory_id)
        if not memory:
            return
        self.access_log.append(
            {
                "memory_id": memory_id,
                "actor": actor,
                "action": action,
                "query_text": query,
                "occurred_at": datetime.now(UTC),
            }
        )

    def export(self) -> list[dict]:
        return [self._public(memory) for memory in self.memories.values()]
