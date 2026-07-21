"""HTTP boundary for Chronicle's engineering-memory system."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AskRequest,
    AskResponse,
    DashboardResponse,
    ExportResponse,
    GraphResponse,
    Memory,
    MemoryCreate,
    MemoryDetail,
    SearchResponse,
    TimelineGroup,
)
from app.services.cockroach_store import CockroachMemoryStore
from app.services.demo_store import DemoMemoryStore
from app.services.embedding import Embedder
from app.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = settings or get_settings()
    embedder = Embedder(runtime)
    store = CockroachMemoryStore(runtime, embedder) if runtime.database_url else DemoMemoryStore(runtime)

    app = FastAPI(
        title="Chronicle API",
        version="0.1.0",
        description="Persistent engineering memory for AI coding agents.",
    )
    app.state.settings = runtime
    app.state.embedder = embedder
    app.state.store = store
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "demo" if runtime.is_demo else "live"}

    @app.get("/api/v1/dashboard", response_model=DashboardResponse)
    def dashboard() -> dict:
        return store.dashboard()

    @app.get("/api/v1/memories", response_model=SearchResponse)
    def search_memories(
        q: str = "",
        mode: str = Query(default="hybrid", pattern="^(semantic|hybrid|keyword)$"),
        limit: int = Query(default=12, ge=1, le=50),
    ) -> dict:
        results = store.search(q, mode, limit)
        note = {
            "semantic": "Ranked by CockroachDB vector similarity in live mode.",
            "keyword": "Ranked by full-text relevance.",
            "hybrid": "Combines semantic similarity with keyword relevance.",
        }[mode]
        return {"query": q, "mode": mode, "results": results, "total": len(results), "retrieval_note": note}

    @app.get("/api/v1/memories/{memory_id}", response_model=MemoryDetail)
    def memory_detail(memory_id: str) -> dict:
        detail = store.detail(memory_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Memory not found")
        store.record_access(memory_id, "chronicle-ui", "inspected")
        return detail

    @app.post("/api/v1/memories", response_model=Memory, status_code=201)
    def create_memory(payload: MemoryCreate) -> dict:
        return store.create_memory(payload)

    @app.get("/api/v1/timeline", response_model=list[TimelineGroup])
    def timeline(limit: int = Query(default=30, ge=1, le=100)) -> list[dict]:
        return store.timeline(limit)

    @app.get("/api/v1/graph/{memory_id}", response_model=GraphResponse)
    def graph(memory_id: str) -> dict:
        result = store.graph(memory_id)
        if not result:
            raise HTTPException(status_code=404, detail="Memory not found")
        return result

    @app.post("/api/v1/ask", response_model=AskResponse)
    def ask(payload: AskRequest) -> dict:
        memories = store.search(payload.question, "hybrid", limit=5)
        if not memories:
            return {
                "answer": "Chronicle has no matching engineering memory yet. Capture the outcome when this work completes.",
                "cited_memory_ids": [],
                "confidence": 0.0,
                "mode": "demo",
            }
        synthesized = embedder.answer(payload.question, memories)
        citations = [memory["id"] for memory in memories[:3]]
        if not synthesized:
            lead = memories[0]
            supporting = memories[1:3]
            support_text = " ".join(memory["summary"] for memory in supporting)
            synthesized = f"{lead['summary']} {support_text}".strip()
        for memory in memories[:3]:
            store.record_access(memory["id"], "chronicle-analyst", "retrieved", payload.question)
        return {
            "answer": synthesized,
            "cited_memory_ids": citations,
            "confidence": round(sum(memory.get("score", 0.75) for memory in memories[:3]) / min(3, len(memories)), 2),
            "mode": "bedrock" if runtime.use_bedrock else "demo",
        }

    @app.post("/api/v1/exports", response_model=ExportResponse)
    def export_memories() -> dict:
        records = store.export()
        if not runtime.s3_export_bucket:
            return {
                "status": "ready",
                "format": "json",
                "location": None,
                "included_memories": len(records),
            }
        import boto3

        key = f"chronicle-exports/{runtime.project_slug}/{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
        boto3.client("s3", region_name=runtime.aws_region).put_object(
            Bucket=runtime.s3_export_bucket,
            Key=key,
            Body=json.dumps(records, default=str, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        return {
            "status": "configured",
            "format": "json",
            "location": f"s3://{runtime.s3_export_bucket}/{key}",
            "included_memories": len(records),
        }

    return app


app = create_app()
