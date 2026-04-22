# New KB Server — Requirements & Specifications

**Status:** Draft
**Depends on:** Phase 1 — Library Manager integration (complete)
**Companion document:** [Architectural Design](lamb-kb-server-design.md)
**Terminology:** Libraries **IMPORT** content (document repository). Knowledge Bases **INGEST** content (chunking + embedding into vector store).

This document describes the **final state** of the system after all phases are complete — what the user can do, not how it's built. The design document covers architecture and phased implementation.

---

## 1. Problem Statement

The current `lamb-kb-server-stable/` handles everything: file upload, ingestion, embedding, vector storage, and querying. This monolithic design makes it hard to extend (new vector DBs, new chunking strategies) and duplicates document handling that the Library Manager now owns.

We need a new KB server that focuses exclusively on chunking, embedding, and vector storage — receiving documents from LAMB, not managing them.

---

## 2. Goals

1. **Separate concerns** — Library Manager owns documents, KB server owns vectors.
2. **Pluggable vector backends** — ChromaDB today, Qdrant or others tomorrow.
3. **Pluggable chunking strategies** — Simple, hierarchical, by-page, by-section.
4. **Citation support** — Every vector chunk carries permalink metadata so RAG results can link back to source documents.
5. **Coexistence** — New KB server runs alongside `lamb-kb-server-stable/` on a different port. No migration required on day one.

---

## 3. Non-Goals

- Migrating existing KB data from `lamb-kb-server-stable/`.
- Replacing `lamb-kb-server-stable/` — it continues running unchanged.
- Internal TLS between services.

---

## 4. Functional Requirements

### 4.1 Knowledge Base Lifecycle

- **FR-1:** Users can create a knowledge base with a locked configuration (chunking strategy, embedding model, vector DB backend). This configuration cannot be changed after creation.
- **FR-2:** Users can delete a knowledge base, which removes all vectors and metadata.
- **FR-3:** Users can update a knowledge base's name and description.
- **FR-4:** Users can list their knowledge bases (owned and shared).
- **FR-5:** Users can share a knowledge base with their organization.

### 4.2 Content Ingestion

- **FR-6:** Users can add library items to a knowledge base. LAMB provides the document content and permalink information to the KB server — the KB server does NOT fetch from the Library Manager directly.
- **FR-7:** Ingestion is asynchronous. Users can poll for processing status.
- **FR-8:** Each ingested chunk carries permalink metadata from the source library item (original file link, page link, full markdown link) for use in RAG citations.
- **FR-9:** Users can remove a library item's vectors from a knowledge base without affecting the library item or other knowledge bases.
- **FR-10:** If a library item is referenced by any knowledge base, LAMB prevents its deletion from the library.

### 4.3 Querying

- **FR-11:** Users can query a knowledge base with a text string. The system embeds the query and performs similarity search.
- **FR-12:** Query results include the chunk text, similarity score, and permalink metadata (source title, page number, links to original/page/markdown).
- **FR-13:** The RAG pipeline can query multiple knowledge bases and merge results by similarity score.

### 4.4 Organization Controls

- **FR-14:** Organization admins can restrict which vector DB backends, embedding models, and chunking strategies are available to their users.
- **FR-15:** Organization config provides default settings for new knowledge bases.
- **FR-16:** Embedding API keys are resolved from organization config by LAMB and sent per-request. The KB server never stores API keys.

### 4.5 Access Control

- **FR-17:** All access control is managed by LAMB. The KB server is an internal service with no user-level authentication.
- **FR-18:** Access follows the same pattern as libraries: owner has full control, shared gives read/query/add-content access, org admins have full access within their org.

---

## 5. Non-Functional Requirements

- **NFR-1:** New KB server runs on port **9092** (different from stable's 9090). Both can run simultaneously.
- **NFR-2:** Only LAMB calls the KB server. Single bearer token auth, no user-level ACL.
- **NFR-3:** Internal Docker network only. No published ports in production.
- **NFR-4:** Embedding API keys held in memory for job/request duration only, then discarded.
- **NFR-5:** Testable end-to-end via programmatic tests (no UI dependency) from day one.
- **NFR-6:** Vector storage is isolated per organization at the filesystem level. Each org has its own directory, and each collection within the org has its own subdirectory.
- **NFR-7:** No artificial storage limits per knowledge base. Disk usage is bounded naturally by library content size and chunking settings. Infrastructure-level limits (disk quotas, cloud billing) are the admin's responsibility, not the application's.
- **NFR-8:** Content updates are not supported. If a library item's content changes, existing KBs that ingested it simply remain stale. There is no automatic re-ingestion or notification. A KB is a snapshot at ingestion time.

---

## 6. Key Interface: LAMB → KB Server Content Delivery

This is the most important interface in the system. When a user adds library items to a knowledge base, LAMB does NOT tell the KB server to "go fetch from the Library Manager." Instead:

1. **LAMB resolves the content** — reads the library item's markdown and metadata.
2. **LAMB sends the content to the KB server** — including the raw text, permalink URLs, and access methods for any linked resources (images, sub-pages, original files).
3. **KB server receives everything it needs** in a single request — no service-to-service calls to Library Manager.

This matters because:
- The KB server has no knowledge of libraries, organizations, or access control.
- Permalinks must be correct from LAMB's perspective (they include org ID and are ACL-enforced).
- RAG results use these permalinks to direct users to the source content — the format must be precise.

### Content Delivery Format

When LAMB calls the KB server's add-content endpoint, it provides for each document:

- **Document text** — the full markdown content to chunk.
- **Document title** — for citation display.
- **Source item ID** — to track which library item produced these vectors.
- **Permalink URLs** — original file, full markdown, per-page links. These are the ACL-enforced LAMB URLs (`/docs/{org}/{lib}/{item}/...`), not Library Manager internal URLs.
- **Embedding credentials** — API key for the embedding model, held for job duration only.

The KB server chunks the text, embeds it, attaches the permalink metadata to each chunk, and stores everything in the vector DB. When query results come back, they carry these permalinks so the frontend can render clickable source citations.

---

## 7. Verification Criteria

The final system must satisfy all of these, regardless of which client (CLI, frontend, API) is used:

1. A user can create a knowledge base with a locked store setup (chunking strategy, embedding model, vector DB backend).
2. A user can list their own and shared knowledge bases.
3. A user can add library items to a knowledge base; processing is asynchronous and status is observable.
4. A user can query a knowledge base and receive results containing chunk text, similarity score, and permalink metadata.
5. A user can remove a specific library item's vectors from a knowledge base without affecting the library item or other knowledge bases.
6. Deleting a library item that is referenced by any knowledge base is blocked with a clear error.
7. A user can delete a knowledge base, which removes all associated vectors.
8. A user can share or unshare a knowledge base with their organization.
9. Organization isolation: users in org A cannot access knowledge bases belonging to org B.
10. Organization admins can restrict allowed vector DB backends, embedding models, and chunking strategies for their users.
11. Query results used by the RAG pipeline include clickable citation links pointing back to the source library content.
