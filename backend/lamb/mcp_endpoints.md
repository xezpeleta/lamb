# LAMB MCP (Model Context Protocol) Server

## Overview

The LAMB MCP server provides a Model Context Protocol interface to the LAMB learning assistant system. This allows external MCP clients to interact with LAMB's assistants, knowledge bases, and tools through a standardized protocol.

**Key Feature**: LAMB MCP exposes assistants as prompt templates that return fully crafted prompts with RAG context, allowing MCP clients to leverage LAMB's educational context while using their own LLM providers.

## Base URL

All MCP endpoints are available under: `/lamb/v1/mcp/`

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

## Available Endpoints

### 1. Initialize MCP Server
**POST** `/lamb/v1/mcp/initialize`

Initialize the MCP server connection and establish capabilities.

**Request Body:**
```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": {
    "resources": {"subscribe": true, "listChanged": true},
    "tools": {"listChanged": true},
    "prompts": {"listChanged": true}
  },
  "clientInfo": {
    "name": "MCP Client",
    "version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": {
    "resources": {"subscribe": true, "listChanged": true},
    "tools": {"listChanged": true},
    "prompts": {"listChanged": true}
  },
  "serverInfo": {
    "name": "LAMB-MCP-Server",
    "version": "0.1.0",
    "protocolVersion": "2024-11-05"
  }
}
```

### 2. List Resources
**GET** `/lamb/v1/mcp/resources/list`

Get available resources from the LAMB system, including all assistants.

**Response:**
```json
{
  "resources": [
    {
      "uri": "lamb://assistants",
      "name": "LAMB Assistants",
      "description": "Access to all LAMB learning assistants",
      "mimeType": "application/json"
    },
    {
      "uri": "lamb://assistant/1",
      "name": "Assistant: Math Helper",
      "description": "A mathematics learning assistant",
      "mimeType": "application/json"
    }
  ]
}
```

### 3. List Tools
**GET** `/lamb/v1/mcp/tools/list`

Get available tools that can be called through the MCP server.

**Response:**
```json
{
  "tools": [
    {
      "name": "create_assistant",
      "description": "Create a new LAMB learning assistant",
      "inputSchema": {
        "type": "object",
        "properties": {
          "name": {"type": "string", "description": "Assistant name"},
          "description": {"type": "string", "description": "Assistant description"},
          "system_prompt": {"type": "string", "description": "System prompt"},
          "prompt_template": {"type": "string", "description": "Prompt template with {user_input} and {context} placeholders"},
          "metadata": {"type": "string", "description": "JSON config for plugins (optional)"}
        },
        "required": ["name", "description", "system_prompt", "prompt_template"]
      }
    },
    {
      "name": "query_assistant",
      "description": "Query a LAMB learning assistant (returns the fully crafted prompt)",
      "inputSchema": {
        "type": "object",
        "properties": {
          "assistant_id": {"type": "integer", "description": "Assistant ID"},
          "query": {"type": "string", "description": "Query text (user_input)"},
          "include_rag": {"type": "boolean", "description": "Include RAG context", "default": true}
        },
        "required": ["assistant_id", "query"]
      }
    },
    {
      "name": "update_assistant",
      "description": "Update an existing LAMB assistant",
      "inputSchema": {
        "type": "object",
        "properties": {
          "assistant_id": {"type": "integer", "description": "Assistant ID"},
          "name": {"type": "string", "description": "New name (optional)"},
          "description": {"type": "string", "description": "New description (optional)"},
          "system_prompt": {"type": "string", "description": "New system prompt (optional)"},
          "prompt_template": {"type": "string", "description": "New prompt template (optional)"}
        },
        "required": ["assistant_id"]
      }
    }
  ]
}
```

### 4. List Prompts
**GET** `/lamb/v1/mcp/prompts/list`

Get available prompt templates from LAMB assistants.

**Response:**
```json
{
  "prompts": [
    {
      "name": "assistant_1_math_helper",
      "description": "A mathematics learning assistant (Assistant ID: 1)",
      "arguments": [
        {"name": "user_input", "description": "The user's input/question", "required": true},
        {"name": "include_rag_context", "description": "Include RAG context from knowledge base", "required": false}
      ]
    },
    {
      "name": "assistant_2_science_tutor",
      "description": "A science learning assistant (Assistant ID: 2)",
      "arguments": [
        {"name": "user_input", "description": "The user's input/question", "required": true}
      ]
    }
  ]
}
```

### 5. Get Prompt
**POST** `/lamb/v1/mcp/prompts/get/{prompt_name}`

Get a processed prompt from an assistant with all substitutions applied.

**Parameters:**
- `prompt_name`: The prompt name from the prompts list (e.g., "assistant_1_math_helper")

**Request Body:**
```json
{
  "user_input": "What is the derivative of x^2?",
  "include_rag_context": true
}
```

**Response:**
```json
{
  "prompt": "You are a helpful mathematics tutor. Please help the student with the following question:\n\nWhat is the derivative of x^2?\n\nRelevant context from knowledge base:\nThe power rule states that d/dx(x^n) = n*x^(n-1)...",
  "metadata": {
    "assistant_id": 1,
    "system_prompt": "You are a helpful mathematics tutor.",
    "template_used": "You are a helpful mathematics tutor. Please help the student with the following question:\n\n{user_input}\n\nRelevant context from knowledge base:\n{context}",
    "rag_context_included": true
  }
}
```

### 6. Call Tool
**POST** `/lamb/v1/mcp/tools/call/{tool_name}`

Execute a specific tool with provided arguments.

#### Create Assistant Example
**POST** `/lamb/v1/mcp/tools/call/create_assistant`

**Request Body:**
```json
{
  "name": "Chemistry Tutor",
  "description": "A chemistry learning assistant",
  "system_prompt": "You are a knowledgeable chemistry tutor who helps students understand chemical concepts.",
  "prompt_template": "Student Question: {user_input}\n\nRelevant Information: {context}\n\nPlease provide a clear and educational response."
}
```

#### Query Assistant Example (Returns Crafted Prompt)
**POST** `/lamb/v1/mcp/tools/call/query_assistant`

**Request Body:**
```json
{
  "assistant_id": 1,
  "query": "Explain photosynthesis",
  "include_rag": true
}
```

**Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"prompt\": \"Student Question: Explain photosynthesis\\n\\nRelevant Information: [RAG context about photosynthesis]\\n\\nPlease provide a clear and educational response.\",\n  \"system_prompt\": \"You are a knowledgeable biology tutor.\",\n  \"original_input\": \"Explain photosynthesis\",\n  \"rag_context\": {...},\n  \"template_used\": \"Student Question: {user_input}\\n\\nRelevant Information: {context}\\n\\nPlease provide a clear and educational response.\"\n}"
    }
  ]
}
```

### 7. Read Resource
**GET** `/lamb/v1/mcp/resources/read?uri={resource_uri}`

Read the content of a specific resource.

**Parameters:**
- `uri`: The resource URI (e.g., "lamb://assistants" or "lamb://assistant/1")

**Response for `lamb://assistants`:**
```json
{
  "contents": [
    {
      "uri": "lamb://assistants",
      "mimeType": "application/json",
      "text": "{\n  \"assistants\": [\n    {\n      \"id\": 1,\n      \"name\": \"Math Helper\",\n      \"description\": \"Mathematics learning assistant\",\n      \"owner\": \"teacher@school.edu\",\n      \"system_prompt\": \"You are a helpful mathematics tutor.\",\n      \"prompt_template\": \"Question: {user_input}\\n\\nContext: {context}\",\n      \"has_rag\": true\n    }\n  ]\n}"
    }
  ]
}
```

### 8. Get Status
**GET** `/lamb/v1/mcp/status`

Get the current status and capabilities of the MCP server.

**Response:**
```json
{
  "status": "active",
  "protocolVersion": "2024-11-05",
  "serverInfo": {
    "name": "LAMB-MCP-Server",
    "version": "0.1.0",
    "description": "Model Context Protocol server for LAMB (Learning Assistant Manager and Builder)"
  },
  "capabilities": {
    "resources": true,
    "tools": true,
    "prompts": true
  },
  "endpoints": {
    "initialize": "/lamb/v1/mcp/initialize",
    "resources": "/lamb/v1/mcp/resources/list",
    "tools": "/lamb/v1/mcp/tools/list",
    "prompts": "/lamb/v1/mcp/prompts/list",
    "get_prompt": "/lamb/v1/mcp/prompts/get/{prompt_name}"
  },
  "statistics": {
    "total_assistants": 5,
    "available_prompt_processors": ["default", "simple_augment"],
    "available_connectors": ["openai", "anthropic"],
    "available_rag_processors": ["owi_rag"],
    "mcp_integration": "active"
  }
}
```

## How It Works

### Assistant as Prompt Template

LAMB assistants are exposed as MCP prompts. Each assistant has:
- A **system prompt**: The system-level instructions
- A **prompt template**: A template with placeholders for `{user_input}` and `{context}`
- **RAG configuration**: Optional retrieval-augmented generation from knowledge bases

When you call a prompt via MCP:
1. Your `user_input` is inserted into the `{user_input}` placeholder
2. If RAG is enabled, relevant context is retrieved and inserted into `{context}`
3. The fully crafted prompt is returned (not executed through an LLM)
4. You can then use this enriched prompt with your own LLM provider

### MCP Architecture

LAMB's MCP implementation is designed as a separate layer that:
- **Uses assistant data** without modifying regular assistant behavior
- **Builds prompts independently** from the regular completion flow
- **Preserves assistant functionality** - assistants continue to work normally through the regular API
- **Provides prompt templates** specifically for MCP clients

This architectural separation ensures that:
- Regular LAMB assistants continue to function normally
- MCP clients get access to prompt templates without affecting the core system
- The same assistant can be used both as a regular assistant (with LLM execution) and as an MCP prompt template

## Testing with curl

### Check MCP Status
```bash
curl -X GET "http://localhost:8000/lamb/v1/mcp/status" \
     -H "Authorization: Bearer YOUR_API_KEY"
```

### List Available Prompts
```bash
curl -X GET "http://localhost:8000/lamb/v1/mcp/prompts/list" \
     -H "Authorization: Bearer YOUR_API_KEY"
```

### Get a Crafted Prompt
```bash
curl -X POST "http://localhost:8000/lamb/v1/mcp/prompts/get/assistant_1_math_helper" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -d '{
       "user_input": "How do I solve quadratic equations?",
       "include_rag_context": true
     }'
```

### Create a New Assistant
```bash
curl -X POST "http://localhost:8000/lamb/v1/mcp/tools/call/create_assistant" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -d '{
       "name": "History Guide",
       "description": "A history learning assistant",
       "system_prompt": "You are a knowledgeable history teacher.",
       "prompt_template": "Student question: {user_input}\n\nHistorical context: {context}\n\nProvide an engaging historical explanation."
     }'
```

## Use Cases

### 1. Educational Chatbots
MCP clients can use LAMB prompts to create educational chatbots that:
- Have consistent pedagogical approaches
- Include relevant course materials via RAG
- Maintain subject-specific contexts

### 2. Custom LLM Integration
Organizations can:
- Use LAMB's prompt engineering with their preferred LLM providers
- Maintain control over LLM selection and API usage
- Benefit from LAMB's educational prompt templates

### 3. Prompt Engineering Workflows
Developers can:
- Test and refine prompts using LAMB's template system
- Compare outputs across different LLMs using the same enriched prompts
- Build prompt libraries for educational applications

## Integration Example

Here's how an MCP client might use LAMB:

```python
# 1. Get available prompts
prompts = mcp_client.list_prompts()

# 2. Select a math assistant prompt
math_prompt = next(p for p in prompts if "math" in p.name)

# 3. Get the crafted prompt with user input
crafted = mcp_client.get_prompt(
    math_prompt.name,
    {
        "user_input": "Explain derivatives",
        "include_rag_context": True
    }
)

# 4. Use the crafted prompt with your LLM
response = your_llm.complete(
    prompt=crafted["prompt"],
    system=crafted["metadata"]["system_prompt"]
)
```

This approach allows you to leverage LAMB's educational expertise while maintaining flexibility in LLM selection and deployment. 