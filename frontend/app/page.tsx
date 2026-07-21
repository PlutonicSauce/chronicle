"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  ChevronDown,
  Command,
  Database,
  Network,
  Search,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";

import { Inspector } from "../components/inspector";
import { MemoryGraph } from "../components/memory-graph";
import { MemoryRow } from "../components/memory-row";
import { Sidebar } from "../components/sidebar";
import { demoDashboard, demoDetail, demoGraph, demoMemories, demoSearch } from "../lib/demo-data";
import type { Dashboard, Graph, Memory, MemoryDetail, SearchMode, SearchResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const views = ["Explorer", "Timeline", "Graph"] as const;
type View = (typeof views)[number];

async function api<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_URL}${path}`);
    if (!response.ok) return fallback;
    return response.json() as Promise<T>;
  } catch {
    return fallback;
  }
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", { notation: "compact" }).format(value);
}

function dayLabel(value: string) {
  const date = value.includes("T") ? new Date(value) : new Date(`${value}T12:00:00`);
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
}

export default function ChroniclePage() {
  const [dashboard, setDashboard] = useState<Dashboard>(demoDashboard);
  const [results, setResults] = useState<Memory[]>(demoSearch.results);
  const [selected, setSelected] = useState<Memory>(demoDetail.memory);
  const [detail, setDetail] = useState<MemoryDetail>(demoDetail);
  const [graph, setGraph] = useState<Graph>(demoGraph);
  const [query, setQuery] = useState(demoSearch.query);
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [view, setView] = useState<View>("Explorer");
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    void api<Dashboard>("/api/v1/dashboard", demoDashboard).then(setDashboard);
    void api<SearchResponse>(
      `/api/v1/memories?q=${encodeURIComponent(demoSearch.query)}&mode=hybrid`,
      demoSearch,
    ).then((payload) => {
      setResults(payload.results);
      const first = payload.results[0];
      if (!first) return;
      setSelected(first);
      const fallbackDetail: MemoryDetail = { memory: first, relationships: [], related_memories: [] };
      const fallbackGraph: Graph = {
        focus_memory_id: first.id,
        nodes: [{ id: first.id, label: first.title, kind: first.source_kind, importance: first.importance, is_focus: true }],
        edges: [],
      };
      void api<MemoryDetail>(`/api/v1/memories/${first.id}`, fallbackDetail).then(setDetail);
      void api<Graph>(`/api/v1/graph/${first.id}`, fallbackGraph).then(setGraph);
    });
  }, []);

  const timelineGroups = useMemo(() => {
    const groups = new Map<string, Memory[]>();
    for (const memory of results) {
      const date = memory.occurred_at.slice(0, 10);
      groups.set(date, [...(groups.get(date) ?? []), memory]);
    }
    return Array.from(groups.entries());
  }, [results]);

  async function selectMemory(memory: Memory) {
    setSelected(memory);
    const fallbackDetail: MemoryDetail = { memory, relationships: [], related_memories: [] };
    const fallbackGraph: Graph = {
      focus_memory_id: memory.id,
      nodes: [{ id: memory.id, label: memory.title, kind: memory.source_kind, importance: memory.importance, is_focus: true }],
      edges: [],
    };
    const [nextDetail, nextGraph] = await Promise.all([
      api<MemoryDetail>(`/api/v1/memories/${memory.id}`, fallbackDetail),
      api<Graph>(`/api/v1/graph/${memory.id}`, fallbackGraph),
    ]);
    setDetail(nextDetail);
    setGraph(nextGraph);
  }

  async function runSearch() {
    setIsSearching(true);
    const fallback: SearchResponse = { ...demoSearch, query, mode };
    const payload = await api<SearchResponse>(
      `/api/v1/memories?q=${encodeURIComponent(query)}&mode=${mode}`,
      fallback,
    );
    setResults(payload.results);
    if (payload.results[0]) await selectMemory(payload.results[0]);
    setIsSearching(false);
  }

  const stats = [
    { label: "Memories", value: formatNumber(dashboard.stats.total_memories), icon: Database },
    { label: "Relationships", value: formatNumber(dashboard.stats.relationships), icon: Network },
    { label: "Confidence", value: `${Math.round(dashboard.stats.high_confidence_ratio * 100)}%`, icon: Sparkles },
    { label: "Agents active", value: String(dashboard.stats.active_agents), icon: Bot },
  ];

  return (
    <main className="app-shell">
      <Sidebar repository={dashboard.repository} />
      <section className="workspace">
        <header className="topbar">
          <div className="breadcrumb"><span>Projects</span><i>/</i><strong>{dashboard.project_name}</strong><ChevronDown size={14} /></div>
          <div className="top-actions">
            <span className={`storage-status ${dashboard.mode}`}><i /> {dashboard.mode === "live" ? "CockroachDB connected" : "seeded demo"}</span>
            <button className="command-button" type="button"><Command size={13} /> K</button>
            <span className="avatar">SK</span>
          </div>
        </header>

        <div className="workspace-scroll">
          <section className="intro">
            <div>
              <span className="overline">Engineering memory · {dashboard.repository}</span>
              <h1>Know why the code is<br /><em>the way it is.</em></h1>
            </div>
            <p>Chronicle turns every meaningful engineering event into durable, searchable context for the agents building your software.</p>
          </section>

          <section className="stats" aria-label="Memory statistics">
            {stats.map(({ label, value, icon: Icon }) => (
              <div className="stat" key={label}>
                <Icon size={15} strokeWidth={1.5} />
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </section>

          <section className="search-section">
            <div className="view-tabs" role="tablist" aria-label="Memory views">
              {views.map((item) => (
                <button
                  className={view === item ? "active" : ""}
                  key={item}
                  role="tab"
                  aria-selected={view === item}
                  type="button"
                  onClick={() => setView(item)}
                >{item}</button>
              ))}
            </div>
            <div className="search-bar">
              <Search size={18} strokeWidth={1.6} />
              <input
                aria-label="Search engineering memory"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => event.key === "Enter" && void runSearch()}
                placeholder="Ask what changed, why, or what failed…"
              />
              <div className="search-controls">
                <SlidersHorizontal size={15} />
                <select aria-label="Search mode" value={mode} onChange={(event) => setMode(event.target.value as SearchMode)}>
                  <option value="hybrid">Hybrid</option>
                  <option value="semantic">Semantic</option>
                  <option value="keyword">Keyword</option>
                </select>
                <button onClick={() => void runSearch()} type="button">{isSearching ? "Searching" : "Search"}</button>
              </div>
            </div>
            <div className="search-note"><Sparkles size={13} /> {mode === "hybrid" ? "Vector + keyword retrieval, ranked in one durable memory system." : `${mode} retrieval across indexed engineering events.`}</div>
          </section>

          {view === "Explorer" ? (
            <section className="content-grid">
              <div className="results-panel">
                <div className="list-heading">
                  <div><span className="overline">Retrieved context</span><h2>{results.length} memories with a reason to exist</h2></div>
                  <span>ordered by relevance</span>
                </div>
                <div className="memory-list">
                  {results.map((memory) => <MemoryRow key={memory.id} memory={memory} selected={selected.id === memory.id} onSelect={(next) => void selectMemory(next)} />)}
                </div>
              </div>
              <aside className="context-panel">
                <MemoryGraph graph={graph} onSelect={(id) => {
                  const memory = results.find((item) => item.id === id) ?? demoMemories.find((item) => item.id === id);
                  if (memory) void selectMemory(memory);
                }} />
                <Inspector detail={detail} />
              </aside>
            </section>
          ) : view === "Timeline" ? (
            <section className="timeline-view">
              <div className="list-heading"><div><span className="overline">Chronological truth</span><h2>The record survives the release.</h2></div><span>{results.length} events</span></div>
              {timelineGroups.map(([date, memories]) => (
                <div className="timeline-day" key={date}>
                  <time>{dayLabel(date)}</time>
                  <div>{memories.map((memory) => <MemoryRow key={memory.id} memory={memory} selected={selected.id === memory.id} onSelect={(next) => void selectMemory(next)} />)}</div>
                </div>
              ))}
            </section>
          ) : (
            <section className="graph-view">
              <div className="list-heading"><div><span className="overline">Causal context</span><h2>Memory is a graph, not a transcript.</h2></div><span>{graph.edges.length} direct links</span></div>
              <MemoryGraph graph={graph} onSelect={(id) => {
                const memory = results.find((item) => item.id === id) ?? demoMemories.find((item) => item.id === id);
                if (memory) void selectMemory(memory);
              }} />
              <div className="graph-explanation"><Activity size={17} /><p>Each edge describes a verified engineering relationship: an experiment that led to a decision, a decision that enabled a fix, or a previous incident that shaped the current implementation.</p></div>
            </section>
          )}

          <section className="activity-section">
            <div className="section-heading"><span className="overline">Recent capture</span><h2>Work your agents will not forget.</h2></div>
            <div className="activity-strip">
              {dashboard.recent_activity.slice(0, 4).map((activity) => (
                <button key={activity.id} type="button" onClick={() => {
                  const memory = results.find((item) => item.id === activity.memory_id) ?? demoMemories.find((item) => item.id === activity.memory_id);
                  if (memory) void selectMemory(memory);
                }}>
                  <span className="activity-dot" />
                  <span><small>{activity.actor} · {dayLabel(activity.occurred_at)}</small><strong>{activity.memory_title}</strong></span>
                </button>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
