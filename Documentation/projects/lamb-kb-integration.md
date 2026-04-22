# LAMB ↔ KB Server Integration Design

**Status:** Draft
**Depends on:** New KB Server ([requirements](lamb-kb-server-requirements.md), [design](lamb-kb-server-design.md))
**Pattern:** Same proxy architecture as Library Manager integration ([Library integration](lamb-library-integration.md))

---

## 1. Goal

Connect the new KB server to LAMB so that users can manage knowledge bases, add library content, and query through `lamb-cli` first (Phase 1) and the Svelte frontend later (Phase 2). LAMB is the orchestrator: it validates permissions, resolves org config, delivers content with permalinks, and proxies all requests.

---

## 2. Scope

### Phase 1 — CLI integration

The core phase. All backend work happens here. No frontend changes.

1. **LAMB database tables** — `knowledge_bases`, `kb_content_links` in LAMB's SQLite DB.
2. **Creator Interface endpoints** — `/creator/knowledge-bases/...` routes that the CLI calls.
3. **KB Server HTTP client** — LAMB-side client that communicates with the new KB server.
4. **Content delivery** — LAMB reads library content + metadata and sends it to the KB server (the KB server does NOT call the Library Manager).
5. **Auth context** — `can_access_kb()` updated to use the new `knowledge_bases` table.
6. **Org config resolution** — Allowed vector DBs, embedding models, chunking strategies, default store setup.
7. **RAG pipeline update** — Updated RAG processors to query the new KB server with embedding credentials.
8. **Library item deletion guard** — Block deletion of library items referenced by `kb_content_links`.
9. **lamb-cli commands** — Updated `lamb kb` commands calling `/creator/knowledge-bases/...`.
10. **Docker Compose** — New `kb-server` service on port 9092.
11. **Testing** — Playwright API-level tests + CLI end-to-end verification.

**Done when:** A user can create KBs, add library content, query, share, and delete through `lamb-cli`, and all requirements verification criteria pass via the CLI.

### Phase 2 — Svelte frontend

Add the KB management UI to the Svelte frontend, following the same pattern as the Libraries frontend.

1. **Service** — `knowledgeBaseServiceV2.js` (or update existing) calling `/creator/knowledge-bases/...`.
2. **Components** — KB list, KB detail with content management, store setup wizard, query test interface, citation link rendering in chat results.
3. **i18n** — `knowledgeBases` keys updated in all locale files (en, es, ca, eu).
4. **Navigation** — KB link in the Sources dropdown (same place as Libraries).
5. **Playwright browser tests** — UI-level E2E tests covering the full KB lifecycle.

**Done when:** A user can perform all KB operations through the browser, RAG query results in the chat interface render clickable citation links, and all requirements verification criteria pass via the UI.

---

## 3. Architecture

```
User → lamb-cli      ─┐
User → Svelte frontend ┼→ LAMB Backend (/creator/knowledge-bases/...) → New KB Server (9092)
                        │         ↓                        ↑
                        │    LAMB DB                  Content + permalinks
                        │    (knowledge_bases,        delivered BY LAMB
                        │     kb_content_links)       (KB does NOT call Library Manager)
```

### Service responsibilities in this integration

| Responsibility | Who |
|---|---|
| User authentication, ACL | LAMB |
| Org config (allowed backends, models, strategies) | LAMB |
| Reading library content + metadata | LAMB |
| Constructing ACL-enforced permalink URLs | LAMB |
| Delivering content to KB server | LAMB |
| Sending embedding credentials per-request | LAMB |
| Audit logging | LAMB |
| Library item deletion guard | LAMB |
| Chunking, embedding, vector storage, queries | KB Server |

---

## 4. Content Delivery Flow

When a user adds library items to a KB:

1. LAMB validates: user can access KB + library items, items are "ready".
2. LAMB reads each library item's markdown content via the Library Manager.
3. LAMB reads each item's metadata to get permalink URLs.
4. LAMB constructs LAMB-scoped permalink URLs (`/docs/{org}/{lib}/{item}/...`).
5. LAMB sends everything to the KB server in a single request: document text, title, source item ID, permalink URLs, and embedding credentials.
6. KB server processes asynchronously: chunk → embed → store.
7. LAMB polls for status, updates `kb_content_links`.

---

## 5. LAMB Database — New Tables

- **knowledge_bases** — KB metadata, locked `store_setup`, owner, sharing, org. Same structure as `libraries` table (UUID primary key, organization_id, is_shared, owner_user_id).
- **kb_content_links** — Many-to-many: which library items are ingested into which KBs. Tracks processing status (pending, processing, completed, failed), chunk count, and job ID.

---

## 6. Creator Interface Endpoints

All under `/creator/knowledge-bases/...`. Same proxy pattern as `/creator/libraries/...`.

### KB lifecycle

- `POST /creator/knowledge-bases` — Create KB with `store_setup`
- `GET /creator/knowledge-bases` — List user's KBs (owned + shared)
- `GET /creator/knowledge-bases/{id}` — KB details + content list
- `PUT /creator/knowledge-bases/{id}` — Update name/description
- `DELETE /creator/knowledge-bases/{id}` — Delete KB
- `PUT /creator/knowledge-bases/{id}/share` — Toggle sharing

### Content management

- `POST /creator/knowledge-bases/{id}/add-content` — Add library items (LAMB delivers content to KB)
- `DELETE /creator/knowledge-bases/{id}/content/{item_id}` — Remove item from KB
- `GET /creator/knowledge-bases/{id}/processing-status` — Processing status

### Query

- `POST /creator/knowledge-bases/{id}/query` — Test query

---

## 7. lamb-cli Commands

```
lamb kb create "Biology KB" --chunking simple --vector-db chromadb
lamb kb list
lamb kb get <kb-id>
lamb kb delete <kb-id>
lamb kb share <kb-id> --enable/--disable
lamb kb add-content <kb-id> --library <lib-id> --items item1,item2
lamb kb remove-content <kb-id> --item <item-id>
lamb kb processing-status <kb-id>
lamb kb query <kb-id> "search text"
```

All commands call `/creator/knowledge-bases/...` endpoints.

### Library item deletion guard (cross-service check)

The existing `lamb library delete-item` command must refuse deletion when the item is referenced by any knowledge base. This verifies the `kb_content_links` guard is working end-to-end.

```
$ lamb library delete-item <lib-id> <item-id> --confirm
Error: Item is used by 2 knowledge base(s). Remove from KBs first:
  - Biology KB (<kb-id-1>)
  - Neuroscience KB (<kb-id-2>)
```

After removing the item from both KBs, the delete succeeds:

```
$ lamb kb remove-content <kb-id-1> --item <item-id>
$ lamb kb remove-content <kb-id-2> --item <item-id>
$ lamb library delete-item <lib-id> <item-id> --confirm
Item <item-id> deleted.
```

This flow must pass in Phase 1 testing before Phase 2 (frontend) begins.

---

## 8. RAG Pipeline Update

The existing RAG processors (`simple_rag.py`, `context_aware_rag.py`) are updated to:

1. Resolve KB server collection ID from the new `knowledge_bases` table.
2. Resolve embedding credentials from org config.
3. Send query to KB server with credentials.
4. Receive results with permalink metadata.
5. Build RAG context with citation links.

Query rewriting (in `context_aware_rag`) stays in LAMB — the KB server receives the final query text.

---

## 9. Library Item Deletion Guard

When a library item is deleted (Phase 1 flow), LAMB checks `kb_content_links` before allowing deletion:

- If the item is referenced by any KB → reject with error: "Item is used by N knowledge base(s). Remove from KBs first."
- If not referenced → proceed with deletion.

---

## 10. Architectural Decisions

### ADR-1: Same proxy pattern as Library Manager integration

`lamb-cli` → `/creator/knowledge-bases/...` → LAMB → KB Server. Proven pattern from Phase 1. LAMB handles auth/ACL/audit, KB server handles computation.

### ADR-2: Content delivered by LAMB, not fetched by KB

LAMB reads library content and sends it to the KB server. The KB server never contacts the Library Manager. This ensures permalinks are LAMB-scoped (ACL-enforced) and keeps the KB server stateless with respect to libraries and orgs.

### ADR-3: Pydantic models for request bodies

JSON request bodies with Pydantic models (same as library endpoints after the Phase 1 review fix). CLI sends JSON, frontend sends JSON, router validates with Pydantic.

---

## 11. Future

- **Migration** from `lamb-kb-server-stable/` — separate effort, not part of Phase 2.
- **Stable retirement** — after migration is validated.
