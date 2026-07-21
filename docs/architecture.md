# Chronicle architecture

Chronicle is a persistent engineering-memory system, not a conversational interface. It captures durable engineering events, links them to the work that produced them, and makes that history retrievable by meaning, keyword, time, and relationship.

## System shape

```text
Coding agents / GitHub events / CI
              |
              v
       FastAPI ingestion API  -----> Amazon Bedrock
              |                         | embeddings + synthesis
              v                         v
       CockroachDB Cloud <--- durable memories, edges, search
              |
      Cloud MCP Server
              |
       Claude Code / Cursor

Next.js workspace <------ FastAPI query API ------> S3 report export
```

The frontend has no database credentials. The API owns ingestion, ranking, authorization, and model calls. An agent can also use the CockroachDB Cloud Managed MCP Server to inspect and safely query the same memory database directly; the repository includes a ready-to-complete Cursor configuration.

## Data model

`projects` scopes every memory. `memories` is the immutable core event record: title, summary, source evidence, actor, repository metadata, scored attributes, tags, and an embedding. `memory_relationships` is a directed, typed edge table for causality, supersession, duplication, and contextual links. `memory_access_log` records agent and human retrieval to make reasoning trails auditable.

The vector index uses a project UUID prefix and a cosine operator class. That matches the most common query shape: "find the nearest memories inside this project", allowing CockroachDB to keep tenant/project filtering and vector retrieval in one consistent system of record. Keyword retrieval uses a stored `TSVECTOR` document and GIN index. Hybrid ranking is calculated in the API from normalized semantic and text relevance scores, keeping the policy easy to explain and adjust.

## Why these choices

- CockroachDB is authoritative: embeddings, operational facts, relationships, and access trails commit together. There is no secondary vector store that can drift from the engineering record.
- Bedrock Titan Text Embeddings V2 is configured at 512 dimensions. Its configurable output size makes it an efficient fit for a latency-sensitive product while CockroachDB enforces vector dimensionality in SQL.
- Bedrock Converse provides an optional synthesis layer that produces a compact answer and cites the retrieved memory IDs. Synthesis is never stored as source truth.
- The API starts in demo mode without cloud credentials, seeded with a realistic incident and architecture history. Setting `DATABASE_URL` and AWS credentials switches to the live integrations.
- S3 exports are deliberately asynchronous/deployable infrastructure rather than a client-side download, so reports can be retained and shared with durable access controls.

## Milestones

1. Define the durable model and demo contract. Complete.
2. Implement and test the API, seeded retrieval, CockroachDB gateway, and Bedrock client.
3. Implement the memory workspace and all principal views.
4. Add operational artifacts: migrations, MCP configuration, containers, AWS deployment guidance, and README.
5. Build and test both applications, then fix every detected issue.

## Technical risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Bedrock model access varies by AWS account and region. | Model IDs and region are configurable; the deterministic demo provider keeps the product runnable locally. |
| Vector indexes must be enabled on the CockroachDB cluster and building them on populated tables has operational constraints. | The migration states the required cluster setting and creates the index before production ingestion. |
| An MCP-connected agent can be powerful. | The config uses a dedicated cluster and the README recommends OAuth/read-only access until write workflows are reviewed. |
| Dense graph layouts can become unreadable. | The initial view renders only direct relationships around the inspected memory, with type-based edges and intentional hierarchy. |
