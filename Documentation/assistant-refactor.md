# Assistant Object Refactoring: api_callback to metadata

## Status Update

### Phase 1: Creator Interface & Frontend ✅ COMPLETED (2024-01-08)

Successfully implemented the following changes:
- Updated `AssistantGetResponse` and `AssistantCreateBody` models to include `metadata` field
- Modified `prepare_assistant_body` to handle metadata as source of truth
- Added logic to populate metadata from api_callback in get_assistant endpoints
- Updated all frontend components to use metadata instead of api_callback
- Removed unused fields from creator interface models
- Tested all functionality - everything working correctly

### Phase 2: Backend Core - Virtual Field Mapping ✅ COMPLETED (2024-01-08)

Successfully implemented virtual field mapping without database changes:
- Added `metadata` property to Assistant class that maps to `api_callback`
- Added comprehensive documentation to `database_manager.py` explaining the mapping
- Updated `add_assistant` and `update_assistant` methods to always set deprecated fields to empty strings
- **Updated all backend code to use `assistant.metadata` instead of `assistant.api_callback`:**
  - `lamb/mcp_router.py`: Updated comments and metadata handling
  - `lamb/assistant_router.py`: Verified correct usage of property mapping
  - `creator_interface/openai_connect.py`: Added fallback logic for backward compatibility
  - `lamb/completions/main.py`: Updated `parse_plugin_config` function
  - `lamb/completions/rag/single_file_rag.py`: Updated to use metadata property
  - `lamb/mcp_endpoints.md`: Updated documentation to reference metadata
  - `lamb/templates/assistants.html`: Added fallback logic and deprecation comments
  - `Documentation/assistant_object_briefing.md`: Comprehensive update with new property and examples
- Tested the implementation - metadata property correctly maps to/from api_callback
- Full backward compatibility maintained - no database migration needed

## Problem Statement

The LAMB system's Assistant object contains a critical design issue that has evolved over time. The field `api_callback` was originally intended to store API callback URLs for future extensibility. However, as the system evolved, this field has been repurposed to store JSON-encoded plugin configuration data, creating several problems:

### Current Issues

1. **Misleading Field Name**: The field `api_callback` suggests it contains a URL or callback endpoint, but it actually contains JSON configuration data like:
   ```json
   {
     "prompt_processor": "simple_augment",
     "connector": "openai",
     "llm": "gpt-4o-mini",
     "rag_processor": "no_rag",
     "file_path": ""
   }
   ```

2. **Unused Legacy Fields**: The database schema contains several fields that are no longer used:
   - `pre_retrieval_endpoint`
   - `post_retrieval_endpoint`
   - `RAG_endpoint` (partially used but mostly deprecated)

3. **Type Confusion**: The field is typed as a string but contains JSON data, requiring constant parsing/stringifying operations throughout the codebase.

4. **Extensibility Limitations**: As we need to store more custom fields, the current approach of having fixed schema fields becomes increasingly problematic.

## Current Database Schema

```sql
CREATE TABLE LAMB_assistants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner TEXT NOT NULL,
    api_callback TEXT,              -- Actually stores JSON config
    system_prompt TEXT,
    prompt_template TEXT,
    RAG_endpoint TEXT,              -- Mostly unused
    RAG_Top_k INTEGER,
    RAG_collections TEXT,
    pre_retrieval_endpoint TEXT,    -- Unused
    post_retrieval_endpoint TEXT    -- Unused
)
```

## Current Usage Analysis

### 1. Backend Core (lamb/)

- **Assistant Class** (`lamb_classes.py`): Defines all fields including unused ones
- **Database Manager** (`database_manager.py`): Handles CRUD operations with all fields
- **Completions System** (`completions/main.py`): Parses `api_callback` as JSON to extract plugin configuration
- **MCP Router** (`mcp_router.py`): Directly parses `api_callback` JSON instead of using the standard parser
- **RAG Processors**: Some (like `single_file_rag.py`) expect specific data in `api_callback`

### 2. Creator Interface (creator_interface/)

- **Assistant Router**: Creates `AssistantGetResponse` model that includes publication fields not in the base Assistant class
- **Response Models**: Mix assistant data with publication data (group_id, group_name, oauth_consumer_name, published_at, published)

### 3. Frontend (svelte-app/)

- **AssistantForm.svelte**: Constructs JSON object and stringifies it for `api_callback`
- **AssistantsList.svelte**: Parses `api_callback` to display configuration
- **Assistant Service**: Handles the field as a string containing JSON

## Proposed Solution

### Phase 1: Creator Interface & Frontend Refactoring

1. **Rename `api_callback` to `metadata`** in:
   - Creator Interface response models
   - Frontend components and services
   - Keep the field as JSON string for now

2. **Remove unused fields** from Creator Interface responses:
   - `pre_retrieval_endpoint`
   - `post_retrieval_endpoint`
   - `RAG_endpoint`

3. **Create a clean separation** between:
   - Core assistant data (id, name, description, owner, system_prompt, prompt_template, metadata)
   - RAG configuration (RAG_Top_k, RAG_collections)
   - Publication data (group_id, group_name, oauth_consumer_name, published_at, published)

### Phase 2: Backend Core Refactoring - Virtual Field Mapping Approach (NO DB CHANGES) ✅ COMPLETED

#### Database Analysis Results

After examining the database schema and existing data:
- The `LAMB_assistants` table has 12 columns including the problematic fields
- Analysis shows 0 records use `RAG_endpoint`, `pre_retrieval_endpoint`, or `post_retrieval_endpoint`
- The `api_callback` field is actively used to store JSON configuration data

#### Chosen Implementation: Virtual Field Mapping

Instead of altering the database schema, we'll implement a virtual field mapping layer:

1. **Database Level**: Keep the existing schema unchanged
   - `api_callback` column continues to store the JSON configuration data
   - Unused columns remain in place but are ignored by the application
   - NO ALTER TABLE statements, NO migrations needed

2. **Application Level Changes**:
   - Add `metadata` property to Assistant class that maps to `api_callback`
   - Update database_manager.py with clear documentation about the mapping
   - Ensure unused fields are always set to empty strings

#### Implementation Details for Phase 2:

##### 1. Update lamb_classes.py:
```python
class Assistant(BaseModel):
    # Existing fields remain unchanged
    api_callback: str  # DEPRECATED: Use metadata property. Kept for DB compatibility.
    
    # These fields are deprecated but kept for DB schema compatibility
    pre_retrieval_endpoint: str  # DEPRECATED: Always empty string
    post_retrieval_endpoint: str  # DEPRECATED: Always empty string
    RAG_endpoint: str  # DEPRECATED: Mostly unused, always empty string
    
    @property
    def metadata(self) -> str:
        """
        Virtual field mapping to api_callback for backward compatibility.
        
        IMPORTANT FOR FUTURE DEVELOPERS:
        - This property provides the semantic name 'metadata' for what's stored in 'api_callback'
        - The DB column remains 'api_callback' to avoid schema migration
        - All new code should use 'metadata' instead of 'api_callback'
        - Contains JSON-encoded plugin configuration
        """
        return self.api_callback
    
    @metadata.setter
    def metadata(self, value: str):
        """Set metadata by updating the underlying api_callback field"""
        self.api_callback = value
```

##### 2. Update database_manager.py - Add header comment:
```python
"""
IMPORTANT: Field Mapping Documentation

The Assistant model uses a virtual field mapping for historical reasons:
- 'metadata' (application level) -> 'api_callback' (database column)
- This mapping avoids database schema changes while providing semantic clarity
- The following fields exist in DB but are DEPRECATED and always empty:
  - pre_retrieval_endpoint
  - post_retrieval_endpoint  
  - RAG_endpoint

When working with this code:
1. Use assistant.metadata in application code
2. Use 'api_callback' in SQL queries (it stores the metadata)
3. Always set deprecated fields to empty strings
"""
```

##### 3. Benefits of This Approach:
- **Zero Database Migration Risk**: No schema changes needed
- **Full Backward Compatibility**: Existing code continues to work
- **Clear Documentation**: Future developers understand the mapping
- **Gradual Migration Path**: Can update DB schema later if needed
- **Semantic Clarity**: Code uses meaningful 'metadata' name

## Implementation Plan

### Step 1: Update Creator Interface Models (creator_interface/assistant_router.py)

```python
class AssistantGetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner: str
    metadata: Optional[str]  # Renamed from api_callback
    system_prompt: Optional[str]
    prompt_template: Optional[str]
    RAG_Top_k: Optional[int]
    RAG_collections: Optional[str]
    # Removed: pre_retrieval_endpoint, post_retrieval_endpoint, RAG_endpoint
    # Publication fields remain
    group_id: Optional[str]
    group_name: Optional[str]
    oauth_consumer_name: Optional[str]
    published_at: Optional[int]
    published: bool
```

### Step 2: Update Creator Interface Logic

- Modify all endpoints to map `api_callback` from backend to `metadata` in responses
- Handle both field names in requests for backward compatibility during transition

### Step 3: Update Frontend Components

1. **Update TypeScript/JSDoc types**:
   ```javascript
   * @property {string} [metadata] - JSON configuration (replaces api_callback)
   ```

2. **Update all components** to use `metadata` instead of `api_callback`

3. **Add migration logic** to handle both field names during transition

### Step 4: Testing Strategy

1. **Unit Tests**: Ensure field mapping works correctly
2. **Integration Tests**: Verify end-to-end flow with new field name
3. **Backward Compatibility Tests**: Ensure existing assistants continue to work

## Benefits of This Refactoring

1. **Clarity**: The field name `metadata` accurately describes its content
2. **Flexibility**: JSON metadata can store any configuration without schema changes
3. **Cleaner API**: Removing unused fields reduces confusion
4. **Future-Proof**: Easy to add new configuration options without database migrations

## Risks and Mitigation

1. **Risk**: Breaking existing integrations
   - **Mitigation**: Support both field names during transition period

2. **Risk**: Data loss during migration
   - **Mitigation**: Careful testing and backup procedures

3. **Risk**: Frontend/Backend mismatch
   - **Mitigation**: Deploy frontend first with support for both field names

## Timeline

- **Phase 1** (Creator Interface & Frontend): 1-2 days
  - Day 1: Update Creator Interface models and logic
  - Day 2: Update Frontend components and test

- **Phase 2** (Backend Core): To be scheduled after Phase 1 success
  - Requires more careful planning due to database migration

## Success Criteria

1. Frontend uses `metadata` field exclusively
2. Creator Interface API returns `metadata` instead of `api_callback`
3. No functionality is broken
4. Code is cleaner and more maintainable
5. Path is clear for Phase 2 backend refactoring