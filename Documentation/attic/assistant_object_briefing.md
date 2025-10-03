# Assistant Object Briefing

## Overview

The Assistant object is the core entity in the LAMB (Learning Assistant Manager and Builder) system. It represents a configured AI assistant with specific prompts, RAG settings, and plugin configurations. This document provides a comprehensive overview of how the Assistant object is defined, stored, retrieved, and used throughout the system.

## Assistant Class Definition

### Location: `backend/lamb/lamb_classes.py`

```python
class Assistant(BaseModel):
    id: int = Field(default=0)
    name: str
    description: str
    owner: str
    api_callback: str  # DEPRECATED: Use metadata property instead. Kept for DB compatibility.
    system_prompt: str
    prompt_template: str
    pre_retrieval_endpoint: str  # DEPRECATED: Always empty string, kept for DB compatibility
    post_retrieval_endpoint: str  # DEPRECATED: Always empty string, kept for DB compatibility
    RAG_endpoint: str  # DEPRECATED: Mostly unused, always empty string, kept for DB compatibility
    RAG_Top_k: int
    RAG_collections: str

    class Config:
        from_attributes = True

    @property
    def metadata(self) -> str:
        """
        Virtual field that maps to api_callback for backward compatibility.
        Contains JSON-encoded plugin configuration.
        """
        return self.api_callback

    @metadata.setter
    def metadata(self, value: str):
        """Set metadata by updating the underlying api_callback field"""
        self.api_callback = value
```

### Key Fields

- **`id`**: Unique identifier (database primary key)
- **`name`**: Human-readable name for the assistant
- **`description`**: Detailed description of the assistant's purpose
- **`owner`**: Email of the user who owns this assistant
- **`metadata`** (property): JSON string containing plugin configuration (preferred way to access configuration data)
- **`api_callback`**: DEPRECATED - Use `metadata` property instead. Kept for database compatibility only.
- **`system_prompt`**: System-level instructions for the LLM
- **`prompt_template`**: Template with placeholders like `{user_input}` and `{context}`
- **`RAG_endpoint`**: Legacy field (mostly unused)
- **`RAG_Top_k`**: Number of top results to retrieve from RAG
- **`RAG_collections`**: Comma-separated list of knowledge base collection IDs
- **`pre_retrieval_endpoint`**: Legacy field (mostly unused)
- **`post_retrieval_endpoint`**: Legacy field (mostly unused)

### Metadata Structure

The `metadata` property (which maps to the `api_callback` database column) contains a JSON string with the following structure:

```json
{
    "prompt_processor": "simple_augment",
    "connector": "openai", 
    "llm": "gpt-4o-mini",
    "rag_processor": "simple_rag",
    "file_path": ""
}
```

## Database Methods

### Location: `backend/lamb/database_manager.py`

### Methods Returning Assistant Objects

#### `get_assistant_by_id(assistant_id: int) -> Optional[Assistant]`
- Returns a single Assistant object by ID
- Used in completions system where Assistant objects are expected
- Converts database row to Assistant object

#### `get_assistant_by_name(assistant_name: str, owner: Optional[str] = None) -> Optional[Assistant]`
- Returns Assistant object by name (optionally filtered by owner)
- Converts database row to Assistant object

### Methods Returning Dictionaries

#### `get_assistant_by_id_with_publication(assistant_id: int) -> Optional[Dict[str, Any]]`
- Returns assistant data as dictionary with publication information
- Includes additional fields: `published`, `group_id`, `group_name`, `oauth_consumer_name`, `published_at`
- **Used in MCP router** to avoid object/dictionary mismatch issues

#### `get_list_of_assistants(owner: str) -> List[Dict[str, Any]]`
- Returns list of assistant dictionaries for a specific owner
- Used for listing assistants in APIs
- Returns dictionaries, not Assistant objects

#### `get_full_list_of_assistants() -> List[Dict[str, Any]]`
- Returns all assistants as dictionaries
- Used for admin/system-wide operations

#### `get_all_assistants_with_publication() -> List[Dict[str, Any]]`
- Returns all assistants with publication data
- Includes publication status and metadata

### CRUD Operations

#### `add_assistant(assistant: Assistant) -> int`
- Creates new assistant in database
- Returns the new assistant ID

#### `update_assistant(assistant_id: int, assistant: Assistant) -> bool`
- Updates existing assistant
- Requires Assistant object as parameter

#### `delete_assistant(assistant_id: int, owner: str) -> bool`
- Deletes assistant (with owner verification)

## Usage in Completions System

### Location: `backend/lamb/completions/main.py`

### Flow Overview

1. **Retrieve Assistant**: `get_assistant_details(assistant_id)` → Returns Assistant object
2. **Parse Plugin Config**: `parse_plugin_config(assistant_details)` → Extracts JSON from `metadata` property
3. **Load Plugins**: `load_and_validate_plugins(plugin_config)` → Loads PPS, connectors, RAG processors
4. **Process RAG**: `get_rag_context()` → Gets context from knowledge base if configured
5. **Process Prompt**: Uses prompt processor to build final messages
6. **Execute**: Uses connector to call LLM

### Key Functions

#### `get_assistant_details(assistant: int) -> Assistant`
```python
def get_assistant_details(assistant: int) -> Any:
    assistant_details = db_manager.get_assistant_by_id(assistant)
    if not assistant_details:
        raise HTTPException(status_code=404, detail=f"Assistant with ID '{assistant}' not found")
    return assistant_details
```

#### `parse_plugin_config(assistant_details: Assistant) -> Dict[str, str]`
```python
def parse_plugin_config(assistant_details) -> Dict[str, str]:
    try:
        if not assistant_details.metadata or assistant_details.metadata.strip() == '':
            callback = {}
        else:
            callback = json.loads(assistant_details.metadata)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Assistant metadata cannot be parsed: {e}")
    
    # Apply defaults for missing keys
    defaults = {
        "prompt_processor": "default",
        "connector": "openai", 
        "llm": "gpt-4",
        "rag_processor": ""
    }
    
    for key in defaults:
        if key not in callback:
            callback[key] = defaults[key]
    
    return callback
```

## Usage in MCP Integration

### Location: `backend/lamb/mcp_router.py`

### Key Differences from Completions

The MCP router uses **dictionary-based** assistant data instead of Assistant objects to avoid type mismatches:

#### Pattern Used in MCP Router

```python
# Get assistant as dictionary (not object)
assistant_data = db_manager.get_assistant_by_id_with_publication(assistant_id)

# Parse metadata manually (stored in api_callback column for backward compatibility)
try:
    if assistant_data.get('api_callback'):  # Database column name
        plugin_config = json.loads(assistant_data['api_callback'])
    else:
        plugin_config = {"rag_processor": "no_rag"}
except json.JSONDecodeError:
    plugin_config = {"rag_processor": "no_rag"}

# Convert to Assistant object only when needed for specific functions
assistant_obj = Assistant(
    id=assistant_data['id'],
    name=assistant_data['name'],
    description=assistant_data.get('description', ''),
    owner=assistant_data['owner'],
    api_callback=assistant_data.get('api_callback', ''),
    system_prompt=assistant_data.get('system_prompt', ''),
    prompt_template=assistant_data.get('prompt_template', ''),
    RAG_endpoint=assistant_data.get('RAG_endpoint', ''),
    RAG_Top_k=assistant_data.get('RAG_Top_k', 5),
    RAG_collections=assistant_data.get('RAG_collections', ''),
    pre_retrieval_endpoint=assistant_data.get('pre_retrieval_endpoint', ''),
    post_retrieval_endpoint=assistant_data.get('post_retrieval_endpoint', '')
)
```

### MCP-Specific Functions

#### `build_mcp_prompt(messages, assistant, rag_context) -> Dict[str, Any]`
- Takes Assistant object as parameter
- Returns structured prompt data for MCP clients
- Includes: original input, system prompt, crafted prompt, RAG context, template used, full messages

## Plugin System Integration

### Prompt Processors (PPS)

Location: `backend/lamb/completions/pps/`

Prompt processors take the assistant's `prompt_template` and user input to create final messages:

```python
def prompt_processor(request, assistant, rag_context):
    # Uses assistant.prompt_template
    # Replaces {user_input} and {context} placeholders
    # Returns formatted messages for LLM
```

### Connectors

Location: `backend/lamb/completions/connectors/`

Connectors handle LLM communication:

```python
def llm_connect(messages, stream, body, llm):
    # Uses the LLM specified in assistant's metadata
    # Sends messages to appropriate LLM provider
    # Returns response in OpenAI-compatible format
```

### RAG Processors

Location: `backend/lamb/completions/rag/`

RAG processors use assistant's RAG configuration:

```python
def rag_processor(messages, assistant):
    # Uses assistant.RAG_collections
    # Uses assistant.RAG_Top_k
    # Queries knowledge base with last user message
    # Returns context and sources
```

## Common Patterns and Best Practices

### 1. Object vs Dictionary Usage

**Use Assistant Objects When:**
- Working with completions system
- Calling functions that expect Assistant objects (like `parse_plugin_config`)
- Need type safety and validation

**Use Dictionary Data When:**
- Working with MCP router
- Need to avoid object/dictionary type mismatches
- Building API responses

### 2. Plugin Configuration Access

**Completions System:**
```python
assistant = get_assistant_details(assistant_id)  # Returns Assistant object
plugin_config = parse_plugin_config(assistant)   # Expects Assistant object
```

**MCP System:**
```python
assistant_data = db_manager.get_assistant_by_id_with_publication(assistant_id)  # Returns dict
plugin_config = json.loads(assistant_data.get('api_callback', '{}'))           # Manual parsing (api_callback stores metadata)
```

### 3. RAG Context Handling

Both systems need to convert to Assistant objects when calling RAG processors:

```python
# If you have dictionary data, convert to object for RAG processing
assistant_obj = Assistant(**assistant_data)
rag_context = get_rag_context(request, rag_processors, rag_processor_name, assistant_obj)
```

## API Endpoints Using Assistants

### Completions API
- `POST /lamb/v1/completions/` - Uses Assistant objects throughout
- `GET /lamb/v1/completions/list` - Lists available processors/connectors

### MCP API
- `GET /lamb/v1/mcp/prompts/list` - Uses dictionary data
- `POST /lamb/v1/mcp/prompts/get/{prompt_name}` - Converts between dict and object as needed
- `GET /lamb/v1/mcp/status` - Uses dictionary data for statistics

### Assistant Management API
- `GET /lamb/v1/assistants/` - Returns dictionary data
- `POST /lamb/v1/assistants/` - Creates Assistant object
- `PUT /lamb/v1/assistants/{id}` - Updates Assistant object
- `DELETE /lamb/v1/assistants/{id}` - Deletes assistant

## Troubleshooting Common Issues

### 1. "'Assistant' object has no attribute 'get'"

**Cause:** Trying to call `.get()` on an Assistant object instead of a dictionary.

**Solution:** Use dictionary-returning database methods or convert object to dictionary.

### 2. "Assistant metadata cannot be parsed"

**Cause:** Invalid JSON in the `metadata` field (stored in `api_callback` database column).

**Solution:** Validate JSON before saving, provide defaults for missing fields.

### 3. "Assistant not found"

**Cause:** Using wrong database method or assistant doesn't exist.

**Solution:** Check if using correct method for return type needed, verify assistant exists and user has access.

## Recent Changes (2024-01-08)

**Assistant Refactoring - api_callback to metadata:**

- Added `metadata` property to Assistant class that maps to `api_callback` database column
- Updated all backend code to use `assistant.metadata` instead of `assistant.api_callback`
- Database schema remains unchanged for backward compatibility
- `api_callback`, `pre_retrieval_endpoint`, `post_retrieval_endpoint`, and `RAG_endpoint` are now deprecated
- All new code should use the `metadata` property for semantic clarity

## Future Improvements

1. ✅ **Rename `api_callback`** to `metadata` for clarity (COMPLETED via virtual property mapping)
2. **Standardize return types** - decide whether to use objects or dictionaries consistently
3. **Add validation** for plugin configurations
4. **Improve error handling** for malformed assistant data
5. **Add caching** for frequently accessed assistants
6. **Create helper functions** to convert between objects and dictionaries safely
7. **Consider database schema migration** to rename `api_callback` column to `metadata` in future major version 