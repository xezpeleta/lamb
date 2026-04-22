# New KB Server — Architectural Design

**Status:** Draft
**Companion document:** [Requirements & Specifications](lamb-kb-server-requirements.md)
**Depends on:** Phase 1 — Library Manager integration (complete)

---

## 1. System Architecture

```
User → lamb-cli      ─┐
User → Svelte frontend ┼→ LAMB Backend (/creator/knowledge-bases/...) → New KB Server (9092)
                        │         ↓                        ↑
                        │    LAMB DB                  Content + permalinks
                        │    (knowledge_bases,        sent BY LAMB
                        │     kb_content_links)       (KB does NOT call Library Manager)
                        │
                        └→ LAMB Backend (/creator/libraries/...) → Library Manager (9091)
```

### Service responsibilities

| Service | Port | Owns | Does NOT do |
|---------|------|------|-------------|
| **LAMB Backend** | 9099 | ACL, org config, orchestration, metadata tables, content delivery to KB | Chunking, embedding, vector storage |
| **New KB Server** | 9092 | Collections, chunking, embedding, vector storage, queries | ACL, org management, file imports, Library Manager calls |
| **Library Manager** | 9091 | Document import, structured content, permalinks | Chunking, embedding, access control |
| **Stable KB Server** | 9090 | Legacy KBs (unchanged, runs alongside) | — |

### Key principle: LAMB delivers content to KB

The KB server never calls the Library Manager. When a user adds library items to a KB:

1. LAMB reads the library item's content and metadata.
2. LAMB constructs the correct permalink URLs (ACL-enforced, org-scoped).
3. LAMB sends the full content + permalinks to the KB server in a single request.
4. KB server chunks, embeds, and stores — receiving everything it needs from LAMB.

This keeps the KB server simple (no knowledge of libraries, orgs, or access control) and ensures permalinks are always correct from LAMB's perspective.

---

## 2. Data Flows

### 2.1 Create Knowledge Base

```
User → lamb kb create "Biology KB" --chunking simple --vector-db chromadb
  → LAMB validates setup against org config (allowed backends, models, strategies)
  → LAMB generates KB UUID
  → LAMB sends to KB Server: create collection with locked store_setup
  → KB Server creates empty collection in vector DB
  → LAMB creates knowledge_bases record (store_setup LOCKED)
  → Returns KB ID to user
```

### 2.2 Add Library Content to KB

```
User → lamb kb add-content <kb-id> --library <lib-id> --items item1,item2
  → LAMB validates: user can access KB + library items, items are "ready"
  → LAMB reads each library item's content (markdown) and metadata (permalinks)
  → LAMB sends to KB Server:
      POST /collections/{id}/add-content
      {
        documents: [
          {
            item_id: "item1",
            title: "Document Title",
            text: "# Full markdown content...",
            permalinks: {
              original: "/docs/{org}/{lib}/{item}/original/file.pdf",
              full_markdown: "/docs/{org}/{lib}/{item}/content/full.md",
              pages: ["/docs/.../pages/page_001.md", ...]
            }
          },
          ...
        ],
        embedding_credentials: { api_key: "sk-...", api_endpoint: "..." }
      }
  → KB Server (async):
      1. For each document: chunk text using collection's strategy
      2. Attach permalink metadata to each chunk
      3. Embed all chunks using collection's model + provided credentials
      4. Store vectors + metadata in vector DB
      5. Discard credentials
  → LAMB polls KB Server for processing status
  → LAMB updates kb_content_links in its DB
```

### 2.3 Query

```
End user message → Assistant has RAG collections
  → LAMB RAG processor:
      1. Resolve KB Server collection ID from knowledge_bases table
      2. Resolve org embedding credentials
      3. Send query to KB Server: POST /collections/{id}/query
  → KB Server:
      1. Embed query text using collection's model + provided credentials
      2. Similarity search in vector DB
      3. Return results with text + permalink metadata
  → LAMB builds RAG context with citations → sends to LLM
  → User sees answer with source links
```

### 2.4 Remove Content / Delete KB

- **Remove content:** LAMB tells KB Server to delete vectors by source_item_id. Library item is unaffected.
- **Delete KB:** LAMB tells KB Server to delete collection. All vectors removed.
- **Delete library item:** LAMB checks kb_content_links first. If item is used by any KB, deletion is blocked.

---

## 3. Knowledge Store Setup

Every knowledge base has a locked configuration set at creation time:

- **Chunking strategy** — simple, hierarchical, by_page, by_section
- **Chunk size / overlap** — controls text splitting granularity
- **Embedding model** — vendor (openai, ollama, local) + model name
- **Vector DB backend** — chromadb, qdrant, etc.

This configuration is immutable. Changing chunking or embedding after vectors exist would make the collection inconsistent. Users who want different settings create a new KB.

---

## 4. Plugin Architecture

### 4.1 Vector DB Plugins

Each plugin implements: create collection, delete collection, store vectors, delete vectors, similarity search, health check.

| Plugin | Backend | Notes |
|--------|---------|-------|
| chromadb | ChromaDB (PersistentClient) | Default, local storage |
| qdrant | Qdrant (local or cloud) | Optional, cloud-ready |

Plugins are enabled/disabled via environment variables and org config.

### 4.2 Chunking Strategies

| Strategy | Description | Query behavior |
|----------|-------------|----------------|
| simple | Recursive character text splitting | Standard similarity |
| hierarchical | Header splitting + parent/child chunks | Parent-child retrieval |
| by_page | Preserves page boundaries from library item pages | Page-aware search |
| by_section | Splits on markdown headers | Section-aware search |

Query strategy is determined by chunking strategy — no separate choice needed.

### 4.3 Embedding Functions

| Vendor | Credentials |
|--------|-------------|
| openai | Per-request API key from LAMB |
| ollama | Server URL (no key needed) |
| local | None (runs in-process) |

---

## 5. Citation via Permalink Propagation

Every chunk stored in the vector DB carries permalink metadata from its source library item:

- **source_item_id** — links back to the library item
- **source_title** — display name for citations
- **page_number** — if applicable (by_page strategy)
- **permalink_original** — link to the original uploaded file
- **permalink_page** — link to the specific page
- **permalink_markdown** — link to the full markdown

These are LAMB-scoped URLs (`/docs/{org}/{lib}/{item}/...`) that enforce ACL when accessed. The frontend renders them as clickable citation links in RAG results.

---

## 6. Access Control

All access control is LAMB's responsibility. The KB server is a pure computation service.

| Action | Owner | Shared user | Org Admin |
|--------|-------|-------------|-----------|
| Create KB | yes | - | yes |
| See KB + query | yes | yes | yes |
| Add library content | yes | yes | yes |
| Remove content | yes | - | yes |
| Delete KB | yes | - | yes |
| Toggle sharing | yes | - | - |

---

## 7. Coexistence with Stable KB Server

The new KB server runs on port **9092**. The stable KB server continues on port **9090**. Both are active simultaneously:

- Existing KBs continue working through the stable server.
- New KBs are created on the new server.
- No migration is required on day one.
- Migration is a future phase: re-import files into libraries, re-ingest into new KBs.

---

## 8. KB Server API Surface

The KB server exposes these endpoints (all require service-level bearer token):

- **Collection management** — create, get, delete collections
- **Content processing** — add documents (text + permalinks + embedding credentials), async with status polling
- **Vector management** — delete vectors by source item ID
- **Query** — embed query text + similarity search, return results with permalink metadata
- **System** — health check, list backends, list chunking strategies

The full API contract is defined at implementation time. The KB server does not expose user-facing endpoints — LAMB proxies all user requests.

---

## 9. Testing Strategy

KB server is tested independently:

- Unit tests for each chunking strategy
- Unit tests for each vector DB plugin
- Integration tests for the full pipeline: receive content → chunk → embed → store → query
- Health and auth tests

LAMB integration testing is covered in the [LAMB ↔ KB Server integration design](lamb-kb-integration.md).

---

## 10. Architectural Decisions

### ADR-1: LAMB delivers content to KB (KB does NOT call Library Manager)

LAMB reads library content and sends it to the KB server. This keeps the KB server stateless with respect to libraries, ensures permalinks are always LAMB-scoped (ACL-enforced), and prevents the KB server from needing Library Manager credentials or knowledge of the document repository.

### ADR-2: Separate port for coexistence (9092)

New KB server runs on 9092, stable runs on 9090. Both active simultaneously. No migration pressure. Users gradually move to new KBs.

### ADR-3: knowledge_store_setup is immutable — no content updates

Locked at creation. Changing chunking or embedding after vectors exist would make the collection inconsistent. Users create new KBs for different settings.

If a library item's content changes (e.g., a file is re-imported), the vectors in any KB that ingested it become stale. The system does nothing about this — there is no automatic re-ingestion, no notification, and no "refresh" operation. A KB is a snapshot of content at ingestion time. If the user wants up-to-date vectors, they create a new KB themselves and ingest the updated content manually.

### ADR-4: Per-request embedding credentials

LAMB sends API keys with each request. KB server holds them for job/request duration only, then discards. Never stored on disk. Same pattern as Library Manager API keys.

### ADR-5: Query strategy tied to chunking strategy

If `chunking_strategy = "hierarchical"`, queries automatically use parent-child retrieval. One choice at creation time, no invalid combinations.

### ADR-6: Access control is LAMB-only

KB server has no concept of users, organizations, or sharing. It receives a bearer token from LAMB (service-level auth) and processes whatever LAMB sends. All ACL decisions happen in LAMB before any KB server call.

### ADR-7: Polling for async processing (webhook as future improvement)

Same as Phase 1 (library imports). KB server exposes status endpoints. LAMB polls. CLI/frontend polls LAMB.

This works well for the current scale, but polling adds latency (up to one poll interval) and unnecessary requests when processing is slow. A future improvement could add an optional webhook/callback mechanism: the KB server would call a LAMB endpoint when a job completes, eliminating polling entirely. This is not done in Phase 2 to keep the implementation simple and consistent with the Library Manager pattern.

### ADR-8: Multi-KB query merging (score normalization as future improvement)

When an assistant references multiple KBs, LAMB queries each independently, merges results by normalized similarity score (0-1), takes overall top_k.

This works well when all KBs use the same embedding model, but similarity scores from different models are not directly comparable (e.g., OpenAI embeddings vs Ollama embeddings produce scores on different scales). A future improvement could implement Reciprocal Rank Fusion (RRF) — merging by position rather than score — which is model-agnostic. For Phase 2, raw score merging is sufficient because most deployments will use a single embedding model across KBs.

### ADR-9: Per-org vector storage isolation

Each organization gets its own storage directory on the KB server. Within an org's directory, each collection (KB) has its own subdirectory. This provides filesystem-level tenant isolation:

```
data/
  org-1/
    collection-aaa/
    collection-bbb/
  org-2/
    collection-ccc/
```

This prevents any possibility of cross-org data leakage at the storage level, and makes it straightforward to calculate per-org storage usage, enforce quotas, or migrate/delete an entire org's data.

### ADR-10: No artificial storage limits

No per-KB or per-org vector storage limits are enforced by the application. Storage usage is bounded naturally by the amount of library content ingested and the chunking settings chosen. Different vector DB backends store data differently (ChromaDB uses more disk than Qdrant for the same vectors), so any application-level limit would be misleading. Infrastructure-level controls (disk quotas, cloud billing tiers) are the admin's responsibility.

### ADR-11: Query rewriting stays in LAMB

The `context_aware_rag` processor rewrites user queries before sending them to the KB server (e.g., expanding abbreviations, adding context from conversation history). This logic stays in LAMB's RAG pipeline, not in the KB server. The KB server receives the final query text and embeds it as-is. This keeps the KB server focused on vector operations and lets LAMB control the full RAG pipeline.
