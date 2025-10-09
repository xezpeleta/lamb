# LAMB Small-Context Documentation

**Purpose:** Focused, task-specific documentation files for AI coding agents

---

## Overview

This folder contains the LAMB architecture documentation broken down into smaller, focused files. Each file is designed to provide enough context for specific coding tasks while minimizing token usage.

The original comprehensive `lamb_architecture.md` remains in the parent directory for human reference.

---

## Documentation Structure

### Frontend Documentation

| File | Purpose | Use When |
|------|---------|----------|
| `frontend_architecture.md` | Frontend overview, structure, routing, config | Setting up frontend, understanding structure |
| `frontend_assistants_management.md` | Assistants UI and workflows | Working on assistant creation/editing UI |
| `frontend_kb_management.md` | Knowledge Base UI and document management | Working on KB interface |
| `frontend_org_management.md` | Admin panels and org management UI | Working on admin/org-admin pages |

### Backend Documentation

| File | Purpose | Use When |
|------|---------|----------|
| `backend_architecture.md` | Backend overview, dual API design, structure | Understanding backend architecture |
| `backend_completions_pipeline.md` | Completion processing, plugins, RAG | Working on completions, plugins, RAG |
| `backend_authentication.md` | Auth flows, tokens, permissions | Working on login, auth, permissions |
| `backend_organizations.md` | Multi-tenancy, org config, roles | Working on organizations, config |
| `backend_knowledge_base.md` | KB server integration, document processing | Working on KB operations |
| `backend_lti_integration.md` | LTI publishing, launches, OAuth | Working on LTI features |

### Reference Documentation

| File | Purpose | Use When |
|------|---------|----------|
| `database_schema.md` | Complete database schema reference | Working with database, queries |

---

## How to Use

### For AI Coding Agents

When given a task:

1. **Identify task category** (frontend, backend, specific feature)
2. **Select relevant docs** (1-3 files usually sufficient)
3. **Read selected docs** for context
4. **Reference other docs** if needed (cross-referenced in each file)
5. **Complete task** with focused context

### Example Task Flows

**Task:** "Add field to assistant creation form"
- Read: `frontend_assistants_management.md`
- Optionally: `backend_architecture.md` (if backend changes needed)

**Task:** "Create custom LLM connector plugin"
- Read: `backend_completions_pipeline.md`
- Optionally: `backend_organizations.md` (for org config)

**Task:** "Fix organization config update endpoint"
- Read: `backend_organizations.md`
- Optionally: `backend_architecture.md`, `database_schema.md`

**Task:** "Add document type support to KB"
- Read: `backend_knowledge_base.md`
- Optionally: `frontend_kb_management.md` (for UI)

---

## File Sizes

Approximate token counts (for reference):

- Frontend files: ~800-1500 tokens each
- Backend files: ~1200-2000 tokens each
- Database schema: ~1500 tokens

**Comparison:** Original `lamb_architecture.md` is ~8000+ tokens

**Savings:** 4-6x reduction by using focused docs

---

## Cross-References

Each file includes a "Related Docs" section at the top listing relevant files. Follow these references when you need additional context.

**Example:**
```
**Related Docs:** `backend_architecture.md`, `backend_completions_pipeline.md`
```

---

## Maintaining Documentation

### When to Update

Update docs when:
- Adding new features
- Changing architecture
- Modifying database schema
- Adding/removing endpoints

### What to Update

- Update relevant focused file(s)
- Add cross-references if needed
- Keep original `lamb_architecture.md` in sync (optional)

### Style Guidelines

- **Concise but complete** - Include what's needed, no more
- **Code examples** - Show real implementations
- **Cross-reference** - Link to related docs
- **Task-oriented** - Focus on "how to do X"

---

## Documentation Map

```
small-context/
├── README.md (this file)
│
├── Frontend/
│   ├── frontend_architecture.md
│   ├── frontend_assistants_management.md
│   ├── frontend_kb_management.md
│   └── frontend_org_management.md
│
├── Backend/
│   ├── backend_architecture.md
│   ├── backend_completions_pipeline.md
│   ├── backend_authentication.md
│   ├── backend_organizations.md
│   ├── backend_knowledge_base.md
│   └── backend_lti_integration.md
│
└── Reference/
    └── database_schema.md
```

---

## Quick Reference

### Common Endpoints

**Authentication:**
- `POST /creator/login` - User login
- `POST /creator/signup` - User signup

**Assistants:**
- `GET /creator/assistant/list` - List assistants
- `POST /creator/assistant/create` - Create assistant
- `POST /creator/assistant/{id}/publish` - Publish assistant

**Knowledge Bases:**
- `GET /creator/knowledgebases/list` - List collections
- `POST /creator/knowledgebases/create` - Create collection
- `POST /creator/knowledgebases/{id}/upload` - Upload document

**Organizations:**
- `GET /creator/admin/organizations` - List organizations
- `POST /creator/admin/organizations/enhanced` - Create organization
- `PUT /creator/admin/organizations/{slug}/config` - Update config

**Completions:**
- `POST /v1/chat/completions` - Generate completion (OpenAI-compatible)
- `GET /v1/models` - List available assistants

### Key Concepts

- **Dual API:** Creator Interface (`/creator`) + LAMB Core (`/lamb/v1`)
- **Organizations:** Multi-tenant isolation with independent configs
- **Plugins:** Prompt processors, connectors, RAG processors
- **OWI Bridge:** Integration with Open WebUI for auth and chat
- **LTI:** Publishing assistants for LMS integration

---

## Getting Help

1. **Check relevant doc** for your task
2. **Follow cross-references** for related info
3. **Consult database schema** for data structures
4. **Read original** `lamb_architecture.md` for comprehensive overview

---

## Version

Created: October 2025  
Source: `lamb_architecture.md` v2.1  
Last Updated: October 2025

