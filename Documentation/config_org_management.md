## Organization-Scoped Defaults, Capabilities, and Connector Behavior

### Context

Assistant creation/editing currently pulls defaults and model lists from environment variables and a static file (`/static/json/defaults.json`). With multi-organization support, these must be sourced from the current organization's configuration. This document defines the phased design to achieve that while keeping the system forward-compatible as defaults grow over time.

**Important Architecture Note**: The system maintains a clear separation of concerns:
- **Environment Variables (`.env`)**: Contains security-sensitive data like API keys, provider URLs, and feature flags. These are loaded on every startup for the system organization.
- **Static Defaults (`/backend/static/json/defaults.json`)**: Contains assistant-specific defaults like prompts, connectors, and RAG settings. These seed the `assistant_defaults` in organization configs.
- **Organization Config**: Stores the merged configuration including both provider settings (from `.env` for system org) and assistant defaults (from `defaults.json`).

### Goals

- **Organization defaults**: Persist all assistant default fields in each organization's config (system org on bootstrap, user orgs on creation; inheritable and editable).
- **Org-aware capabilities**: Assistant create/edit UIs must use the organization's enabled connectors and models, not static defaults.
- **Resilient connector execution**: When a requested model is not enabled, gracefully fallback to the organization's default model or an allowed alternative rather than failing.

### Implementation Status

- **Phase 1**: ✅ COMPLETED - Organization-scoped assistant defaults are persisted and inherited
- **Phase 2**: ✅ COMPLETED - Org-aware capabilities and defaults endpoints implemented, UI integrated
- **Phase 3**: ✅ COMPLETED - Connector runtime fallback logic implemented


## Phase 1 — Persist organization-scoped assistant defaults ✅

### Directives

- **System bootstrap**: When the special system organization (slug `lamb`) is created/synced, populate an `assistant_defaults` object inside its `config` by reading from `/static/json/defaults.json`.
  - On each startup sync, keep the existing object shape and only populate missing keys from the file. Never remove unknown/custom keys.
  - Treat the defaults file as seed values for the system org; org admins can diverge.

- **Organization creation**: New organizations inherit `assistant_defaults` by deep-copying the system org's current `assistant_defaults` at creation time.
  - This provides an immediate, consistent baseline without requiring manual edits.

- **Dynamic field management**: Defaults will grow over time. The backend stores `assistant_defaults` as an open schema (no rigid validation of unknown keys). The UI should render/edit keys dynamically and preserve unknown keys on roundtrips.

### Implementation Details

**Files Modified:**
- `backend/lamb/database_manager.py`:
  - Added `_load_assistant_defaults_from_file()` - Loads defaults from `/backend/static/json/defaults.json`
  - Added `_ensure_assistant_defaults_in_config()` - Merges new keys without overwriting existing values
  - Modified `create_system_organization()` - Seeds assistant_defaults on creation
  - Modified `sync_system_org_with_env()` - Ensures assistant_defaults are preserved and updated
  - Modified `create_organization()` - Inherits from `get_system_org_config_as_baseline()` instead of minimal config
  - Added `get_user_organizations()` - Support for multi-org user queries

**Key Changes:**
- System organization now automatically loads assistant_defaults from the static file on creation
- During sync operations, new keys are added while preserving existing customizations
- New organizations inherit the complete configuration including assistant_defaults from the system org

**Important: Environment Variable Behavior**
- The system organization (`lamb`) is special - it loads critical configuration from `.env` on every startup:
  - API keys (OpenAI, etc.) from environment variables
  - Provider configurations (`_load_providers_from_env()`)
  - Knowledge base settings (`_load_kb_config_from_env()`)
  - Feature flags (`_load_features_from_env()`)
- The `assistant_defaults` are loaded from `/backend/static/json/defaults.json`, NOT from `.env`
- This dual-source approach ensures:
  - Security-sensitive data (API keys) remain in `.env` and are refreshed on startup
  - Assistant defaults can be customized per-organization without affecting credentials
  - System org always has the latest environment configuration

### Storage schema (within organization `config`)

```json
{
  "assistant_defaults": {
    "system_prompt": "...",
    "prompt_template": "...",
    "prompt_processor": "simple_augment",
    "connector": "openai",
    "llm": "gpt-4o-mini",
    "rag_processor": "no_rag",
    "RAG_Top_k": 3,
    "rag_placeholders": ["{context}", "{user_input}"]
    /* Future keys welcome; preserve unknown keys */
  }
}
```

Notes:
- Keys mirror `/static/json/defaults.json` and may increase over time.
- Values must be valid for the organization (e.g., `connector` must be enabled in the org, `llm` must be among org models for that connector). Validation should warn and auto-correct to safe values where possible.

### Management endpoints (admin-only)

**Implemented Endpoints:**
- `GET  /lamb/v1/organizations/{slug}/assistant-defaults` → returns `assistant_defaults` for that org (in `backend/lamb/organization_router.py`)
- `PUT  /lamb/v1/organizations/{slug}/assistant-defaults` → replaces `assistant_defaults` (preserves unknown keys as provided) (in `backend/lamb/organization_router.py`)
- `GET  /creator/admin/organizations/{slug}/assistant-defaults` → Admin UI endpoint that fetches assistant_defaults (in `backend/creator_interface/organization_router.py`)
- `PUT  /creator/admin/organizations/{slug}/assistant-defaults` → Admin UI endpoint to update assistant_defaults (in `backend/creator_interface/organization_router.py`)

**Note:** The creator_interface endpoints forward requests to the lamb API endpoints for consistency.


## Phase 2 — Use organization system capabilities and defaults in Assistant Forms ✅

### Directives

- **Capabilities must be org-aware**: The capabilities endpoint used by the frontend must return connector/model data computed for the current user's organization (derived from the bearer token). No static/env-only lists.
  - Update the capabilities handler to resolve models via org context (e.g., pass `assistant_owner`/user email to connector discovery functions).

- **Defaults must be org-aware**: The Assistant form should fetch organization defaults from a new endpoint instead of `/static/json/defaults.json`.

### Implementation Details

**Backend Changes:**

1. **Org-aware Capabilities** (`backend/lamb/completions/main.py`):
   - Modified `GET /lamb/v1/completions/list` to accept Authorization header
   - Extracts user email via `OwiUserManager.get_user_auth()`
   - Passes `assistant_owner=<email>` to each connector's `get_available_llms()`
   - Returns organization-specific model lists

2. **Assistant Defaults Endpoints**:
   - `GET /creator/assistant/defaults` (`backend/creator_interface/assistant_router.py`):
     - Resolves current user's organization via database
     - Forwards to `/lamb/v1/organizations/{slug}/assistant-defaults`
     - Returns organization-specific defaults
   - `PUT /creator/organizations/{slug}/assistant-defaults` (`backend/creator_interface/assistant_router.py`):
     - Proxy endpoint for UI to update assistant defaults
     - Forwards to lamb API for consistency

**Frontend Changes** (`frontend/svelte-app`):

1. **Assistant Config Store** (`src/lib/stores/assistantConfigStore.js`):
   - Updated to fetch capabilities with Authorization header
   - Switched from static `/static/json/defaults.json` to `GET /creator/assistant/defaults`
   - Maintains caching and fallback behavior

2. **Org Admin UI** (`src/routes/org-admin/+page.svelte`):
   - Added "Assistant Defaults" section to Settings tab
   - JSON editor for viewing/editing assistant_defaults
   - Save/Reload functionality with validation
   - Success/error messaging

**Key Features:**
- Dynamic JSON editing preserves unknown keys
- Real-time validation of JSON syntax
- Organization-scoped defaults properly loaded and displayed
- Integration with existing authentication flow


## Phase 3 — Resilient connector behavior at runtime ✅

### Directives

- **Model resolution and fallback** (applies to each connector, e.g., OpenAI, Ollama):
  1. Resolve the organization’s provider config for the assistant owner (api key, base url, `models`, `default_model`, `enabled`).
  2. If the requested `llm` is not in the org’s `models` (or not enabled):
     - Prefer `default_model` if present and allowed.
     - Otherwise, choose the first allowed model from `models`.
     - Log a warning and proceed (avoid failing), unless the provider is disabled or no models are available.
  3. If provider config is missing for a non-system org, return a clear error indicating the org must configure the provider.
  4. For the system org, legacy fallback to environment variables remains supported (compatibility mode), with explicit logging.

### Implementation Details

**Files Modified:**
- `backend/lamb/completions/connectors/openai.py`:
  - Added model resolution and fallback logic in `llm_connect()`
  - Checks if requested model is in organization's enabled models
  - Falls back to org default_model, then first available model
  - Logs warnings when fallback occurs
  - Raises error only when no models are available

- `backend/lamb/completions/connectors/ollama.py`:
  - Implemented same fallback logic as OpenAI
  - More lenient when no models configured (Ollama can discover models)
  - Proper error messages and logging

**Fallback Chain:**
1. **Requested Model**: Use if available in org's enabled models
2. **Organization Default**: Use org's `default_model` if available
3. **First Available**: Use first model from org's enabled models list
4. **Error**: Raise clear error if no models available (OpenAI only)

**Logging Added:**
- Model fallback warnings with specific details
- Configuration source indicators (org vs env)
- Console output shows fallback status
- Clear error messages when fallback chain exhausted

### Expected runtime behavior

- ✅ Executing assistants "just work" with the organization's configuration
- ✅ Non-enabled models automatically fall back to org's default or first allowed model
- ✅ Clear logging shows configuration source and fallback usage
- ✅ System org maintains environment variable compatibility
- ✅ Graceful error handling when no models available


## Validation and error handling

- When writing `assistant_defaults`, validate references:
  - Connector exists and is enabled for the org.
  - Default model exists within the connector’s model list.
  - Invalid references should be auto-corrected to a safe default (and surfaced in response as warnings) rather than rejected.

- At runtime, connectors should raise meaningful errors only when:
  - The provider is explicitly disabled for the org, or
  - There is no available model after fallback attempts, or
  - Credentials are missing/invalid for a non-system org.


## Rollout plan

1. Implement Phase 1 storage and admin endpoints. On startup, seed system org `assistant_defaults` from `/static/json/defaults.json` if missing. On org creation, inherit from system org.
2. Switch the Assistant form store to use the new org-aware endpoints (capabilities and defaults).
3. Adjust connectors to implement the fallback logic (requested → default_model → first allowed). Keep environment fallback only for the system org.
4. Add logs and metrics to monitor config sources and fallback usage.


## Acceptance criteria

- ✅ Creating a new organization results in `config.assistant_defaults` populated from the system org at that time.
- ✅ Admins can GET org `assistant_defaults` without losing unknown keys.
- ✅ Admins can PUT org `assistant_defaults` without losing unknown keys.
- ✅ Assistant create/edit forms show connector models and defaults reflecting the current user's organization (not `/static/json/defaults.json`).
- ✅ Running an assistant with an invalid/non-enabled model uses a safe fallback model and succeeds, with a warning logged.
- ✅ System org behavior remains backward compatible with environment variables, with explicit logs indicating fallback usage.

## Known Issues

1. **Save Assistant Defaults (FIXED)**:
   - ✅ Added missing PUT endpoint `/creator/admin/organizations/{slug}/assistant-defaults` to creator_interface
   - ✅ Frontend can now successfully save assistant defaults changes
   - ✅ All UI integration now works properly

2. **Minor Enhancements Needed**:
   - Add validation warnings for invalid connector/model references in UI
   - Consider adding org config validation endpoint
   - Performance monitoring for config resolution at scale


## Summary of Implementation

### What Was Accomplished

**Phase 1 (✅ Complete)**:
- System organization automatically seeds `assistant_defaults` from `/backend/static/json/defaults.json`
- System organization continues to load API keys and provider configs from `.env` on every startup
- New organizations inherit complete configuration including assistant_defaults from system org
- Helper methods ensure new keys are merged without overwriting customizations
- Database manager properly handles multi-org user relationships
- Clear separation: `.env` for credentials/API keys, `defaults.json` for assistant defaults

**Phase 2 (✅ Complete)**:
- Capabilities endpoint is now organization-aware, passing user context to connectors
- Assistant defaults endpoints created for both reading and updating
- Frontend assistant config store switched from static file to org-aware endpoints
- Org Admin UI includes full Assistant Defaults management section
- JSON editor with validation, preserving unknown keys
- Fixed missing PUT endpoint in creator_interface for save functionality

**Phase 3 (✅ Complete)**:
- OpenAI connector implements full model fallback chain
- Ollama connector implements full model fallback chain
- Comprehensive logging for configuration sources and fallbacks
- Clear console output showing fallback status
- Error handling when no models available
- System organization maintains environment variable compatibility

**Remaining Work**:
1. Add validation warnings for invalid connector/model references in UI
2. Performance monitoring for config resolution at scale
3. Consider adding org config validation endpoint for comprehensive validation

### Files Changed Summary

**Backend**:
- `backend/lamb/database_manager.py` - Core organization config management
- `backend/lamb/organization_router.py` - Assistant defaults API endpoints
- `backend/lamb/completions/main.py` - Org-aware capabilities
- `backend/lamb/completions/connectors/openai.py` - OpenAI model fallback logic
- `backend/lamb/completions/connectors/ollama.py` - Ollama model fallback logic
- `backend/creator_interface/assistant_router.py` - User-facing defaults endpoints
- `backend/creator_interface/organization_router.py` - Admin management endpoints, assistant defaults endpoints

**Frontend**:
- `frontend/svelte-app/src/lib/stores/assistantConfigStore.js` - Org-aware data fetching
- `frontend/svelte-app/src/routes/org-admin/+page.svelte` - Assistant Defaults UI

## Notes on future expansion

- Additional defaults (e.g., per-connector UI hints, per-RAG plugin parameters, temperature/top_p presets) can be added under `assistant_defaults` without schema migrations.
- Consider adding a lightweight validator that returns warnings and suggested corrections alongside the stored defaults to help admins maintain consistency with enabled capabilities.
- The open schema design allows for organization-specific customizations without breaking compatibility.


