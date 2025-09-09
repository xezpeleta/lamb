# Learning Assistants: Data Structures and Application Flow

## Overview

This document outlines the data structures, endpoints, and application flow for the Learning Assistants feature in the LAMB v4 application. It serves as a reference for developers working on the frontend components that interact with assistant data retrieved from the `/creator/assistant/...` proxy endpoints.

## Assistant Data Structure

Learning Assistants retrieved via the creator interface backend have a structure defined by the `AssistantGetResponse` model.

### Common Properties

All assistant instances share these base properties:

```json
{
  "id": 1,                                   // Unique identifier
  "name": "assistant_name",                  // Display name (prefixed with creator ID, e.g., "1_My Assistant")
  "description": "Description text",         // Brief description
  "owner": "user@example.com",               // Owner email
  "system_prompt": "System prompt text...",  // System instructions for the assistant
  "prompt_template": "Template with {user_input} and {context} placeholders...",
  "group_id": "uuid-string",                 // Group identifier (if published)
  "group_name": "group_name",                // Group name (if published)
  "oauth_consumer_name": "null",             // OAuth consumer (usually "null" if published via creator interface)
  "published_at": 1678886400,                // Publication timestamp (Unix epoch integer, null if unpublished)
  "published": true                          // Publication status (boolean)
}
```

### RAG Configuration Properties

In addition to the common properties, the assistant object includes several top-level fields related to RAG configuration:

```json
{
  // ... common properties ...
  "api_callback": "{"prompt_processor":"simple_augment","connector":"openai","llm":"gpt-4o","rag_processor":"simple_rag"}", // JSON string containing internal configuration like rag_processor, llm, connector, and file_path (for single_file_rag)
  "RAG_endpoint": "https://api.company.com/rag", // Top-level field
  "RAG_Top_k": 5,                               // Top-level field
  "RAG_collections": "collection1,collection2", // Top-level field
  "pre_retrieval_endpoint": "https://api.company.com/pre-retrieval", // Top-level field
  "post_retrieval_endpoint": "https://api.company.com/post-retrieval" // Top-level field
}
```

**Key Points:**

*   The `api_callback` field is a JSON **string**. The frontend needs to parse this string to access internal details like `rag_processor`, `llm`, `connector`, and `file_path` (when applicable).
*   The fields `RAG_endpoint`, `RAG_Top_k`, `RAG_collections`, `pre_retrieval_endpoint`, and `post_retrieval_endpoint` are separate, **top-level** properties on the assistant object itself.

### Examples by RAG Type

Here are examples illustrating the structure for different `rag_processor` types found within the parsed `api_callback` string.

#### 1. Simple RAG Assistant (`rag_processor: "simple_rag"`)

```json
{
  "id": 1,
  "name": "1_Simple_RAG_Helper",
  "description": "Uses KB collections.",
  "owner": "creator@example.com",
  "system_prompt": "Answer based on the provided documents.",
  "prompt_template": "",
  "group_id": "group_uuid_abc",
  "group_name": "assistant_1",
  "oauth_consumer_name": "null",
  "published_at": 1678886400,
  "published": true,
  // --- RAG Specific ---
  "api_callback": "{\"prompt_processor\":\"simple_augment\",\"connector\":\"openai\",\"llm\":\"gpt-4o\",\"rag_processor\":\"simple_rag\"}", // Contains rag_processor
  "RAG_endpoint": "https://api.company.com/rag",
  "RAG_Top_k": 5,
  "RAG_collections": "kb_uuid_1,kb_uuid_2", // Relevant for simple_rag
  "pre_retrieval_endpoint": null,
  "post_retrieval_endpoint": null
}
```

#### 2. Single File RAG Assistant (`rag_processor: "single_file_rag"`)

```json
{
  "id": 2,
  "name": "1_Single_File_Helper",
  "description": "Uses a specific PDF.",
  "owner": "creator@example.com",
  "system_prompt": "Answer based on the single file.",
  "prompt_template": "",
  "group_id": "group_uuid_def",
  "group_name": "assistant_2",
  "oauth_consumer_name": "null",
  "published_at": 1678886401,
  "published": true,
  // --- RAG Specific ---
  "api_callback": "{\"prompt_processor\":\"simple_augment\",\"connector\":\"openai\",\"llm\":\"gpt-4o\",\"rag_processor\":\"single_file_rag\",\"file_path\":\"path/to/file.pdf\"}", // Contains rag_processor and file_path
  "RAG_endpoint": null,          // Usually null/unused for single_file_rag
  "RAG_Top_k": null,             // Usually null/unused for single_file_rag
  "RAG_collections": null,       // Usually null/unused for single_file_rag
  "pre_retrieval_endpoint": null,
  "post_retrieval_endpoint": null
}
```

#### 3. No RAG Assistant (`rag_processor: "no_rag"`)

```json
{
  "id": 3,
  "name": "1_No_RAG_Helper",
  "description": "Standard LLM assistant.",
  "owner": "creator@example.com",
  "system_prompt": "You are a helpful assistant.",
  "prompt_template": "",
  "group_id": "group_uuid_ghi",
  "group_name": "assistant_3",
  "oauth_consumer_name": "null",
  "published_at": 1678886402,
  "published": true,
  // --- RAG Specific ---
  "api_callback": "{\"prompt_processor\":\"simple_augment\",\"connector\":\"openai\",\"llm\":\"gpt-4o-mini\",\"rag_processor\":\"no_rag\"}", // Contains rag_processor
  "RAG_endpoint": null,          // Usually null/unused for no_rag
  "RAG_Top_k": null,             // Usually null/unused for no_rag
  "RAG_collections": null,       // Usually null/unused for no_rag
  "pre_retrieval_endpoint": null,
  "post_retrieval_endpoint": null
}
```

## Frontend Components

### AssistantsList Component

This component displays a table of all available assistants retrieved from `/creator/assistant/get_assistants` with columns for:
- Assistant Details (name, description)
- Configuration (e.g., parsed `rag_processor` from `api_callback`, LLM model)
- Status (Published/Unpublished)
- Actions (buttons for view detail, edit, delete, etc.)

### AssistantDetail Component

This component displays detailed information about a specific assistant retrieved from `/creator/assistant/get_assistant/{id}`:

1.  **Prompt Configuration Section**
    *   System Prompt (`system_prompt` field)
    *   Prompt Template (`prompt_template` field)

2.  **Basic Information Section**
    *   ID (`id`), Name (`name`), Description (`description`)
    *   Owner (`owner`), Published At (`published_at`), Published (`published`)
    *   Group ID (`group_id`), Group Name (`group_name`)

3.  **Technical Configuration Section**
    *   Prompt Processor (from parsed `api_callback`)
    *   Connector (from parsed `api_callback`)
    *   Language Model (from parsed `api_callback`)

4.  **RAG Configuration Section** (conditionally rendered based on `rag_processor` from parsed `api_callback`)
    *   RAG Processor Type (from parsed `api_callback`, displayed for all types)
    *   For Simple RAG (`simple_rag`): Top K (`RAG_Top_k` field) and Collections (`RAG_collections` field)
    *   For Single File RAG (`single_file_rag`): File Path (from parsed `api_callback`, clickable link)
    *   For No RAG (`no_rag`): Explanatory message indicating no RAG is used.

## Application Flow

1.  **Listing Assistants**
    *   Frontend calls `/creator/assistant/get_assistants` endpoint.
    *   AssistantsList component renders table with data, potentially parsing `api_callback` for display columns.
    *   User clicks a row or action button to view details.

2.  **Viewing Assistant Details**
    *   Frontend calls `/creator/assistant/get_assistant/{id}` endpoint.
    *   The `api_callback` string is parsed into a JSON object.
    *   AssistantDetail component determines the `rag_processor` type from the parsed `api_callback`.
    *   Component reads other fields (like `system_prompt`, `RAG_Top_k`, `RAG_collections`) directly from the main assistant object.
    *   Component conditionally renders RAG sections based on the parsed `rag_processor` and displays the relevant fields (e.g., `RAG_Top_k`, `RAG_collections` for simple RAG; `file_path` for single file RAG).

3.  **File Access for Single File RAG**
    *   Files referenced by `file_path` are assumed to be accessible via a specific URL structure (e.g., served from a static directory like `/static/public/` as mentioned, or via a dedicated file download endpoint). The exact mechanism needs confirmation.
    *   When user clicks the file path link, the frontend should construct the correct URL to open/download the file.

## RAG Processor Types (Identified within `api_callback`)

1.  **simple_rag**
    *   Uses collections of documents for retrieval.
    *   Requires `RAG_Top_k` and `RAG_collections` fields on the main assistant object.
    *   May use `pre_retrieval_endpoint`/`post_retrieval_endpoint`.

2.  **single_file_rag**
    *   Uses a single document file for retrieval.
    *   Requires `file_path` within the parsed `api_callback`.
    *   Other top-level RAG fields (`RAG_Top_k`, `RAG_collections`, etc.) are typically unused.

3.  **no_rag**
    *   Does not use retrieval augmentation.
    *   Relies solely on the language model's knowledge.
    *   Top-level RAG fields are typically unused.

## Best Practices

1.  **Error Handling**
    *   Always check if `api_callback` exists and is a non-empty string before attempting to parse it.
    *   Use try/catch when parsing the `api_callback` JSON string to handle potential errors (malformed JSON).
    *   Provide sensible default values or display indicators if essential properties (like `rag_processor`) are missing after parsing.

2.  **Conditional Rendering**
    *   Reliably determine the `rag_processor` from the parsed `api_callback`.
    *   Use this type to conditionally display the correct UI sections and data fields (`RAG_Top_k`, `RAG_collections`, `file_path`).

3.  **User Experience**
    *   Make file paths clickable and ensure they link to the correct file resource URL.
    *   Use clear labels.

## Future Considerations

1.  **Additional RAG Processor Types**
    *   The system is designed to be extensible for new RAG processor types
    *   Component logic should be updated when new types are added

2.  **Enhanced File Handling**
    *   Preview capabilities for different file types
    *   Support for multiple files in RAG configuration

3.  **Configuration Validation**
    *   Frontend validation for required fields based on RAG type
    *   Feedback for incomplete or invalid configurations
