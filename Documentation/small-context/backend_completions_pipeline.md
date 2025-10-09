# Backend: Completions Pipeline

**Purpose:** How LAMB processes chat completion requests with plugins, RAG, and LLM connectors  
**Related Docs:** `backend_architecture.md`, `backend_knowledge_base.md`, `backend_organizations.md`

---

## Overview

The completions pipeline is LAMB's core feature - processing user messages through configurable plugins to generate AI responses. It supports:
- Multiple LLM providers (OpenAI, Ollama, etc.)
- RAG (Retrieval-Augmented Generation) with Knowledge Bases
- Pluggable prompt processors
- Streaming and non-streaming responses
- Organization-specific configurations

---

## Request Flow

```
Client/OWI
  │
  │ POST /v1/chat/completions
  │ { model: "lamb_assistant.1", messages: [...], stream: false }
  ▼
Main Entry Point (backend/main.py)
  │
  │ Route to run_lamb_assistant()
  ▼
Completions Module (backend/lamb/completions/main.py)
  │
  ├─ 1. Parse model ID → assistant_id
  ├─ 2. Load assistant from database
  ├─ 3. Parse plugin config from metadata
  ├─ 4. Load plugins (PPS, Connector, RAG)
  ├─ 5. Execute RAG processor (if configured)
  ├─ 6. Execute prompt processor (PPS)
  ├─ 7. Execute LLM connector
  └─ 8. Return/stream response
  ▼
LLM Provider (OpenAI, Ollama, etc.)
  │
  │ Generate response
  ▼
Client/OWI
```

---

## Plugin Architecture

### Plugin Types

1. **Prompt Processors (PPS)** - Transform and augment messages before LLM
2. **Connectors** - Connect to LLM providers
3. **RAG Processors** - Retrieve context from Knowledge Bases

### Plugin Loading

**Location:** `/backend/lamb/completions/`

```python
def load_plugins(plugin_type: str) -> Dict[str, Any]:
    """
    Dynamically load all plugins of a specific type
    
    Args:
        plugin_type: 'pps', 'connectors', or 'rag'
    
    Returns:
        Dict mapping plugin name to function
    """
    plugins = {}
    plugin_dir = os.path.join(os.path.dirname(__file__), plugin_type)
    
    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    os.path.join(plugin_dir, filename)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get the main function based on plugin type
                if plugin_type == "pps":
                    func = getattr(module, "prompt_processor", None)
                elif plugin_type == "connectors":
                    func = getattr(module, "llm_connect", None)
                elif plugin_type == "rag":
                    func = getattr(module, "rag_processor", None)
                
                if func:
                    plugins[module_name] = func
            except Exception as e:
                logger.error(f"Error loading {plugin_type}/{module_name}: {e}")
    
    return plugins
```

**Plugins are loaded once at module import time for performance**

---

## Step-by-Step Processing

### Step 1: Parse Model ID

```python
def parse_model_id(model: str) -> int:
    """
    Extract assistant ID from model string
    
    Args:
        model: "lamb_assistant.{id}" format
    
    Returns:
        assistant_id as integer
    
    Raises:
        ValueError if format is invalid
    """
    if not model.startswith("lamb_assistant."):
        raise ValueError(f"Invalid model format: {model}")
    
    try:
        assistant_id = int(model.split("lamb_assistant.")[1])
        return assistant_id
    except (IndexError, ValueError):
        raise ValueError(f"Invalid assistant ID in model: {model}")
```

---

### Step 2: Load Assistant

```python
def get_assistant_details(assistant_id: int) -> Assistant:
    """
    Retrieve assistant from database
    
    Returns assistant object with all configuration:
    - name, description
    - system_prompt, prompt_template
    - metadata (plugin configuration)
    - RAG_collections, RAG_Top_k
    - owner (for org config resolution)
    """
    db_manager = LambDatabaseManager()
    assistant = db_manager.get_assistant_by_id(assistant_id)
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return assistant
```

---

### Step 3: Parse Plugin Configuration

```python
def parse_plugin_config(assistant: Assistant) -> Dict[str, str]:
    """
    Extract plugin configuration from assistant metadata
    
    Metadata field is stored in 'api_callback' column but accessed as 'metadata'
    
    Returns:
        {
            "prompt_processor": "simple_augment",
            "connector": "openai",
            "llm": "gpt-4o-mini",
            "rag_processor": "simple_rag"
        }
    """
    default_config = {
        "prompt_processor": "simple_augment",
        "connector": "openai",
        "llm": None,
        "rag_processor": ""
    }
    
    # metadata field is mapped to api_callback column
    metadata_str = getattr(assistant, 'metadata', None) or getattr(assistant, 'api_callback', None)
    
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
            default_config.update(metadata)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse metadata for assistant {assistant.id}")
    
    return default_config
```

**Important:** The `metadata` field in application code maps to `api_callback` column in database. This avoids schema changes while providing semantic clarity.

---

### Step 4: Load and Validate Plugins

```python
def load_and_validate_plugins(plugin_config: Dict[str, str]):
    """
    Load plugins and verify configured plugins exist
    
    Raises:
        ValueError if any configured plugin is not found
    """
    pps = load_plugins("pps")
    connectors = load_plugins("connectors")
    rag_processors = load_plugins("rag")
    
    # Validate configured plugins exist
    if plugin_config["prompt_processor"] not in pps:
        raise ValueError(f"PPS '{plugin_config['prompt_processor']}' not found")
    
    if plugin_config["connector"] not in connectors:
        raise ValueError(f"Connector '{plugin_config['connector']}' not found")
    
    if plugin_config["rag_processor"] and plugin_config["rag_processor"] not in rag_processors:
        raise ValueError(f"RAG processor '{plugin_config['rag_processor']}' not found")
    
    return pps, connectors, rag_processors
```

---

### Step 5: Execute RAG Processor (Optional)

```python
def get_rag_context(
    request: Dict[str, Any],
    rag_processors: Dict[str, Any],
    rag_processor: str,
    assistant: Assistant
) -> Any:
    """
    Execute RAG processor to get relevant context
    
    Returns:
        {
            "context": "formatted context text",
            "sources": [{"source": "file.pdf", "page": 3}]
        }
    """
    if not rag_processor:
        return None
    
    messages = request.get('messages', [])
    rag_context = rag_processors[rag_processor](
        messages=messages,
        assistant=assistant
    )
    return rag_context
```

**Example RAG Processor (`simple_rag.py`):**

```python
def rag_processor(messages: List[Dict], assistant: Assistant = None):
    """
    Query Knowledge Base for relevant context
    """
    # Extract last user message
    last_user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    
    if not last_user_message or not assistant.RAG_collections:
        return {"context": "", "sources": []}
    
    # Get organization-specific KB server configuration
    config_resolver = OrganizationConfigResolver(assistant.owner)
    kb_config = config_resolver.get_kb_server_config()
    
    kb_server_url = kb_config.get("url")
    kb_api_key = kb_config.get("api_key")
    
    # Parse collections
    collections = [c.strip() for c in assistant.RAG_collections.split(',') if c.strip()]
    top_k = getattr(assistant, 'RAG_Top_k', 3)
    
    # Query each collection
    all_results = []
    for collection_id in collections:
        try:
            response = requests.post(
                f"{kb_server_url}/api/collection/{collection_id}/query",
                json={"query": last_user_message, "top_k": top_k},
                headers={"Authorization": f"Bearer {kb_api_key}"}
            )
            if response.ok:
                data = response.json()
                all_results.extend(data.get("results", []))
        except Exception as e:
            logger.error(f"RAG query failed for collection {collection_id}: {e}")
    
    # Format context
    context_parts = []
    sources = []
    for i, result in enumerate(all_results):
        context_parts.append(f"[{i+1}] {result['text']}")
        sources.append({
            "index": i+1,
            "source": result.get('metadata', {}).get('source', 'Unknown'),
            "page": result.get('metadata', {}).get('page', 'N/A')
        })
    
    context = "\n\n".join(context_parts)
    
    return {
        "context": context,
        "sources": sources
    }
```

---

### Step 6: Execute Prompt Processor

```python
def process_completion_request(
    request: Dict[str, Any],
    assistant: Assistant,
    plugin_config: Dict[str, str],
    rag_context: Any,
    pps: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Execute prompt processor to augment messages
    
    Returns:
        List of message dicts with 'role' and 'content'
    """
    pps_func = pps[plugin_config["prompt_processor"]]
    messages = pps_func(
        request=request,
        assistant=assistant,
        rag_context=rag_context
    )
    return messages
```

**Example Prompt Processor (`simple_augment.py`):**

```python
def prompt_processor(
    request: Dict[str, Any],
    assistant: Optional[Assistant] = None,
    rag_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Augment messages with system prompt and RAG context
    """
    messages = []
    
    # Add system prompt
    if assistant and assistant.system_prompt:
        system_content = assistant.system_prompt
        
        # Inject RAG context if available
        if rag_context and rag_context.get("context"):
            system_content += f"\n\nRelevant information:\n{rag_context['context']}"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
    
    # Add user messages from request
    for msg in request.get("messages", []):
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Apply prompt template to last user message if configured
    if assistant and assistant.prompt_template and messages:
        last_msg = messages[-1]
        if last_msg["role"] == "user":
            template = assistant.prompt_template
            last_msg["content"] = template.format(user_message=last_msg["content"])
    
    return messages
```

---

### Step 7: Execute LLM Connector

```python
async def run_lamb_assistant(
    request: Dict[str, Any],
    assistant: int,
    headers: Optional[Dict[str, str]] = None
):
    """
    Execute completion pipeline
    """
    assistant_details = get_assistant_details(assistant)
    plugin_config = parse_plugin_config(assistant_details)
    pps, connectors, rag_processors = load_and_validate_plugins(plugin_config)
    rag_context = get_rag_context(request, rag_processors, plugin_config["rag_processor"], assistant_details)
    messages = process_completion_request(request, assistant_details, plugin_config, rag_context, pps)
    stream = request.get("stream", False)
    llm = plugin_config.get("llm")
    
    # Get connector function
    connector_func = connectors[plugin_config["connector"]]
    
    # Call connector
    llm_response = await connector_func(
        messages=messages,
        stream=stream,
        body=request,
        llm=llm,
        assistant_owner=assistant_details.owner
    )
    
    if stream:
        # Return async generator for streaming
        return StreamingResponse(llm_response, media_type="text/event-stream")
    else:
        # Return JSON response
        return JSONResponse(content=llm_response)
```

**Example Connector (`openai.py`):**

```python
async def llm_connect(
    messages: list,
    stream: bool = False,
    body: Dict[str, Any] = None,
    llm: str = None,
    assistant_owner: Optional[str] = None
):
    """
    Connect to OpenAI API (organization-aware)
    """
    # Get organization-specific configuration
    api_key = None
    base_url = None
    default_model = "gpt-4o-mini"
    
    if assistant_owner:
        config_resolver = OrganizationConfigResolver(assistant_owner)
        openai_config = config_resolver.get_provider_config("openai")
        
        if openai_config:
            api_key = openai_config.get("api_key")
            base_url = openai_config.get("base_url")
            default_model = openai_config.get("default_model", "gpt-4o-mini")
    
    # Fallback to environment variables
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    if not api_key:
        raise ValueError("No OpenAI API key found")
    
    # Model resolution
    resolved_model = llm or default_model
    
    # Create client
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    # Prepare parameters
    params = body.copy() if body else {}
    params["model"] = resolved_model
    params["messages"] = messages
    params["stream"] = stream
    
    if stream:
        # Return async generator
        async def generate_stream():
            stream_obj = await client.chat.completions.create(**params)
            async for chunk in stream_obj:
                yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
        
        return generate_stream()
    else:
        # Return completion
        response = await client.chat.completions.create(**params)
        return response.model_dump()
```

---

## Organization-Specific Configuration

### OrganizationConfigResolver

**File:** `/backend/lamb/completions/org_config_resolver.py`

```python
class OrganizationConfigResolver:
    def __init__(self, user_email: str):
        """
        Initialize with user email to determine organization
        """
        self.db_manager = LambDatabaseManager()
        self.user = self.db_manager.get_creator_user_by_email(user_email)
        
        if not self.user:
            raise ValueError(f"User not found: {user_email}")
        
        self.organization = self.db_manager.get_user_organization(self.user['id'])
        
        if not self.organization:
            # Fallback to system organization
            self.organization = self.db_manager.get_organization_by_slug("lamb")
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific provider (openai, ollama, etc.)
        
        Returns:
            {
                "enabled": true,
                "api_key": "sk-...",
                "base_url": "https://api.openai.com/v1",
                "default_model": "gpt-4o-mini",
                "models": ["gpt-4o", "gpt-4o-mini"]
            }
        """
        config = self.organization.get('config', {})
        setups = config.get('setups', {})
        default_setup = setups.get('default', {})
        providers = default_setup.get('providers', {})
        return providers.get(provider_name)
    
    def get_kb_server_config(self) -> Dict:
        """
        Get Knowledge Base server configuration
        
        Returns:
            {
                "url": "http://localhost:9090",
                "api_key": "kb-api-key"
            }
        """
        config = self.organization.get('config', {})
        kb_config = config.get('kb_server', {})
        
        # Fallback to environment variables
        if not kb_config.get('url'):
            kb_config = {
                'url': os.getenv('KB_SERVER_URL', 'http://localhost:9090'),
                'api_key': os.getenv('KB_API_KEY', '')
            }
        
        return kb_config
```

**Usage in Plugins:**

```python
# In connector
config_resolver = OrganizationConfigResolver(assistant_owner)
openai_config = config_resolver.get_provider_config("openai")
api_key = openai_config.get("api_key")

# In RAG processor
config_resolver = OrganizationConfigResolver(assistant.owner)
kb_config = config_resolver.get_kb_server_config()
kb_server_url = kb_config.get("url")
```

See `backend_organizations.md` for organization config structure.

---

## Available Plugins

### Prompt Processors

**Location:** `/backend/lamb/completions/pps/`

| Plugin | Function | Description |
|--------|----------|-------------|
| `simple_augment` | `prompt_processor()` | Adds system prompt, injects RAG context, applies template |

### Connectors

**Location:** `/backend/lamb/completions/connectors/`

| Plugin | Function | Description |
|--------|----------|-------------|
| `openai` | `llm_connect()` | OpenAI API (org-aware) |
| `ollama` | `llm_connect()` | Ollama local models (org-aware) |
| `bypass` | `llm_connect()` | Testing connector (returns messages) |

### RAG Processors

**Location:** `/backend/lamb/completions/rag/`

| Plugin | Function | Description |
|--------|----------|-------------|
| `simple_rag` | `rag_processor()` | Queries KB server, formats context with sources |
| `no_rag` | `rag_processor()` | Returns empty context (disable RAG) |

---

## Creating Custom Plugins

### Example: Custom Prompt Processor

```python
# /backend/lamb/completions/pps/my_processor.py

def prompt_processor(request, assistant=None, rag_context=None):
    """
    Custom prompt processor
    
    Args:
        request: Original completion request
        assistant: Assistant configuration
        rag_context: Retrieved RAG context
    
    Returns:
        List of message dicts
    """
    messages = []
    
    # Your custom logic here
    # Example: Add custom system prompt formatting
    if assistant and assistant.system_prompt:
        custom_prompt = f"<SYSTEM>\n{assistant.system_prompt}\n</SYSTEM>"
        messages.append({"role": "system", "content": custom_prompt})
    
    # Add user messages
    for msg in request.get("messages", []):
        messages.append(msg)
    
    return messages
```

**No registration needed - plugins auto-load at startup**

### Example: Custom Connector

```python
# /backend/lamb/completions/connectors/my_llm.py

async def llm_connect(messages, stream=False, body=None, llm=None, assistant_owner=None):
    """
    Custom LLM connector
    
    Args:
        messages: Processed messages from PPS
        stream: Whether to stream response
        body: Original request body
        llm: Specific model to use
        assistant_owner: Owner email (for org config)
    
    Returns:
        AsyncGenerator[str] if stream=True (SSE format)
        Dict if stream=False (OpenAI format)
    """
    # Get org config if needed
    if assistant_owner:
        config_resolver = OrganizationConfigResolver(assistant_owner)
        my_config = config_resolver.get_provider_config("my_llm")
        api_key = my_config.get("api_key")
    
    # Your connector logic here
    # Call your LLM API
    # Format response in OpenAI-compatible format
    
    if stream:
        async def generate():
            # Yield SSE format chunks
            yield "data: {json}\n\n"
            yield "data: [DONE]\n\n"
        return generate()
    else:
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": llm or "default",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Response text"
                },
                "finish_reason": "stop"
            }]
        }
```

---

## Streaming vs Non-Streaming

### Non-Streaming

**Request:**
```json
{
  "model": "lamb_assistant.1",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1678886400,
  "model": "lamb_assistant.1",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }]
}
```

### Streaming

**Request:**
```json
{
  "model": "lamb_assistant.1",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}
```

**Response (SSE):**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1678886400,"model":"lamb_assistant.1","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1678886400,"model":"lamb_assistant.1","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1678886400,"model":"lamb_assistant.1","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1678886400,"model":"lamb_assistant.1","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid model format" | Wrong model ID | Use `lamb_assistant.{id}` |
| "Assistant not found" | Invalid assistant ID | Check assistant exists |
| "PPS not found" | Unknown plugin | Check plugin file exists |
| "No API key found" | Missing LLM config | Configure org or env vars |
| "RAG query failed" | KB server down | Check KB server status |

### Error Response Format

```json
{
  "detail": "Error message"
}
```

---

## Performance Considerations

### Plugin Loading

- Plugins loaded once at module import (not per request)
- Cached in memory for fast access
- Hot reload requires server restart

### RAG Queries

- Parallel queries to multiple collections
- Typical query time: 200-500ms
- Consider Top K value (more = slower)

### Streaming Benefits

- Reduces time-to-first-token
- Better user experience for long responses
- Lower memory usage on backend

---

## Related Documentation

- **Backend Architecture:** `backend_architecture.md`
- **Knowledge Base Integration:** `backend_knowledge_base.md`
- **Organizations:** `backend_organizations.md`
- **Frontend Assistant Management:** `frontend_assistants_management.md`

