from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SearchMode = Literal["semantic", "hybrid", "keyword"]


class Memory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    summary: str
    source_kind: str
    source_url: str | None = None
    occurred_at: datetime
    created_at: datetime
    tags: list[str]
    confidence: float
    importance: float
    created_by: str
    repository: str
    commit_hash: str | None = None
    branch: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None


class Relationship(BaseModel):
    from_memory_id: str
    to_memory_id: str
    relationship_kind: str
    confidence: float


class MemoryDetail(BaseModel):
    memory: Memory
    relationships: list[Relationship]
    related_memories: list[Memory]


class MemoryCreate(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    summary: str = Field(min_length=10, max_length=8000)
    source_kind: str = Field(min_length=2, max_length=48)
    source_url: str | None = None
    occurred_at: datetime
    tags: list[str] = Field(default_factory=list, max_length=12)
    confidence: float = Field(ge=0, le=1)
    importance: float = Field(ge=0, le=1)
    created_by: str = Field(min_length=2, max_length=120)
    repository: str
    commit_hash: str | None = None
    branch: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    results: list[Memory]
    total: int
    retrieval_note: str


class TimelineGroup(BaseModel):
    date: str
    memories: list[Memory]


class GraphNode(BaseModel):
    id: str
    label: str
    kind: str
    importance: float
    is_focus: bool = False


class GraphResponse(BaseModel):
    focus_memory_id: str
    nodes: list[GraphNode]
    edges: list[Relationship]


class DashboardStats(BaseModel):
    total_memories: int
    relationships: int
    high_confidence_ratio: float
    active_agents: int


class ActivityItem(BaseModel):
    id: str
    action: str
    actor: str
    occurred_at: datetime
    memory_id: str
    memory_title: str


class DashboardResponse(BaseModel):
    project_name: str
    project_slug: str
    repository: str
    stats: DashboardStats
    recent_activity: list[ActivityItem]
    featured_memories: list[Memory]
    mode: Literal["demo", "live"]


class AskRequest(BaseModel):
    question: str = Field(min_length=4, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    cited_memory_ids: list[str]
    confidence: float
    mode: Literal["demo", "bedrock"]


class ExportResponse(BaseModel):
    status: Literal["ready", "configured"]
    format: str
    location: str | None = None
    included_memories: int
