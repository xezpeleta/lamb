# Frontend: Knowledge Base Management

**Purpose:** UI components for managing document collections and RAG integration  
**Related Docs:** `frontend_architecture.md`, `backend_knowledge_base.md`, `frontend_assistants_management.md`

---

## Overview

The Knowledge Base (KB) management interface allows creators to:
- Create document collections
- Upload documents (PDF, Word, Markdown, TXT, JSON)
- View collection contents
- Test semantic search queries
- Delete collections

Collections can be linked to assistants for RAG-enhanced responses.

---

## Key Components

### KnowledgeBasesList.svelte

**Location:** `/src/lib/components/KnowledgeBasesList.svelte`

**Purpose:** Display user's Knowledge Base collections

**Features:**
- Grid view of collections
- Document count per collection
- Quick actions: View, Upload, Delete
- Search/filter by name

**Data Structure:**

```javascript
{
    id: "collection-uuid",
    name: "CS101 Lectures",
    description: "Computer Science 101 materials",
    document_count: 15,
    created_at: 1678886400,
    user_email: "prof@university.edu",
    organization: "cs_department"
}
```

---

### KnowledgeBaseDetail.svelte

**Location:** `/src/lib/components/KnowledgeBaseDetail.svelte`

**Purpose:** View collection details and manage documents

**Features:**
- List documents in collection
- Upload new documents
- Delete documents
- Test queries
- View chunk count

**Usage:**

```svelte
<script>
    import KnowledgeBaseDetail from '$lib/components/KnowledgeBaseDetail.svelte';
    import { page } from '$app/stores';
    
    const collectionId = $page.params.id;
</script>

<KnowledgeBaseDetail {collectionId} />
```

---

### KBCreateModal.svelte

**Location:** `/src/lib/components/KBCreateModal.svelte`

**Purpose:** Create new Knowledge Base collection

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | Text | Yes | Collection display name |
| Description | Textarea | No | Purpose/content description |

**Create Flow:**

```javascript
async function createCollection() {
    if (!name) {
        alert('Name is required');
        return;
    }
    
    try {
        const result = await knowledgeBaseService.create(
            $userStore.token,
            {
                collection_name: name,
                description: description
            }
        );
        
        // Navigate to new collection
        goto(`/knowledgebases/${result.id}`);
    } catch (error) {
        alert('Failed to create collection: ' + error.message);
    }
}
```

---

### DocumentUpload.svelte

**Location:** `/src/lib/components/DocumentUpload.svelte`

**Purpose:** Upload documents to collection

**Supported Formats:**
- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Markdown (`.md`)
- Plain text (`.txt`)
- JSON (`.json`)

**Features:**
- Drag-and-drop upload
- Multiple file selection
- Progress indicator
- Upload status per file

**Implementation:**

```svelte
<script>
    let files = [];
    let uploading = false;
    let uploadProgress = {};
    
    async function handleUpload() {
        uploading = true;
        
        for (const file of files) {
            try {
                uploadProgress[file.name] = 'uploading';
                
                await knowledgeBaseService.uploadDocument(
                    $userStore.token,
                    collectionId,
                    file
                );
                
                uploadProgress[file.name] = 'success';
            } catch (error) {
                uploadProgress[file.name] = 'error';
                console.error(`Failed to upload ${file.name}:`, error);
            }
        }
        
        uploading = false;
        
        // Refresh collection
        await loadCollection();
    }
</script>

<input 
    type="file" 
    multiple 
    accept=".pdf,.docx,.md,.txt,.json"
    on:change={handleFileSelect}
/>

<button on:click={handleUpload} disabled={uploading || files.length === 0}>
    {uploading ? 'Uploading...' : 'Upload Documents'}
</button>

{#each files as file}
    <div class="file-item">
        <span>{file.name}</span>
        <span class="status status-{uploadProgress[file.name]}">
            {uploadProgress[file.name] || 'pending'}
        </span>
    </div>
{/each}
```

---

### QueryTester.svelte

**Location:** `/src/lib/components/QueryTester.svelte`

**Purpose:** Test semantic search on collection

**Features:**
- Enter query text
- Adjust Top K results
- View matching chunks
- See relevance scores
- Display source metadata

**Usage:**

```svelte
<QueryTester collectionId={selectedCollectionId} />
```

**Implementation:**

```javascript
async function testQuery() {
    if (!queryText) return;
    
    loading = true;
    try {
        const response = await knowledgeBaseService.query(
            $userStore.token,
            collectionId,
            queryText,
            topK
        );
        
        results = response.results.map(r => ({
            text: r.text,
            source: r.metadata.source,
            page: r.metadata.page,
            distance: r.distance.toFixed(3)
        }));
    } catch (error) {
        alert('Query failed: ' + error.message);
    } finally {
        loading = false;
    }
}
```

**Results Display:**

```svelte
{#each results as result}
    <div class="result-card">
        <div class="result-header">
            <span class="source">{result.source}</span>
            {#if result.page}
                <span class="page">Page {result.page}</span>
            {/if}
            <span class="distance">Score: {result.distance}</span>
        </div>
        <div class="result-text">
            {result.text}
        </div>
    </div>
{/each}
```

---

## Service Layer

### knowledgeBaseService.js

**Location:** `/src/lib/services/knowledgeBaseService.js`

**Methods:**

```javascript
import axios from 'axios';
import { getConfig } from '../config.js';

const config = getConfig();
const API_URL = `${config.api.lambServer}/creator/knowledgebases`;

export const knowledgeBaseService = {
    // List collections
    async list(token) {
        const response = await axios.get(`${API_URL}/list`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Get collection details
    async get(token, collectionId) {
        const response = await axios.get(`${API_URL}/${collectionId}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Create collection
    async create(token, data) {
        const response = await axios.post(`${API_URL}/create`, data, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Upload document
    async uploadDocument(token, collectionId, file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(
            `${API_URL}/${collectionId}/upload`,
            formData,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            }
        );
        return response.data;
    },
    
    // Query collection
    async query(token, collectionId, queryText, topK = 5) {
        const response = await axios.get(
            `${API_URL}/${collectionId}/query`,
            {
                params: { q: queryText, top_k: topK },
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    },
    
    // Delete collection
    async delete(token, collectionId) {
        const response = await axios.delete(
            `${API_URL}/${collectionId}`,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    },
    
    // List documents in collection
    async listDocuments(token, collectionId) {
        const response = await axios.get(
            `${API_URL}/${collectionId}/documents`,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    }
};
```

---

## User Workflows

### Creating a Knowledge Base

1. Navigate to `/knowledgebases`
2. Click "Create Knowledge Base"
3. Enter name and description
4. Click "Create"
5. Upload documents to new collection

### Uploading Documents

1. Open collection detail page
2. Click "Upload Documents"
3. Select or drag-and-drop files
4. Wait for processing
5. View uploaded documents list

**Processing Steps (Backend):**
- Extract text from document
- Split into chunks
- Generate embeddings
- Store in ChromaDB

See `backend_knowledge_base.md` for technical details.

### Testing Queries

1. Open collection detail page
2. Click "Test Query"
3. Enter search text
4. Adjust Top K if needed
5. View matching chunks with sources

**Use Case:** Verify collection has relevant content before linking to assistant

### Linking to Assistant

1. Edit or create assistant
2. Enable RAG processor
3. Select Knowledge Base(s) from dropdown
4. Set Top K results
5. Test assistant chat to verify RAG works

---

## Integration with Assistants

### RAG Configuration

When creating/editing an assistant:

```svelte
<script>
    let enableRAG = false;
    let selectedCollections = [];
    let topK = 3;
    
    $: if (enableRAG) {
        $assistantConfigStore.metadata.rag_processor = 'simple_rag';
        $assistantConfigStore.RAG_Top_k = topK;
    } else {
        $assistantConfigStore.metadata.rag_processor = '';
        $assistantConfigStore.RAG_collections = '';
    }
    
    $: $assistantConfigStore.RAG_collections = selectedCollections.join(',');
</script>

<label>
    <input type="checkbox" bind:checked={enableRAG} />
    Enable RAG (Retrieval-Augmented Generation)
</label>

{#if enableRAG}
    <label>
        Knowledge Bases
        <select multiple bind:value={selectedCollections}>
            {#each knowledgeBases as kb}
                <option value={kb.id}>{kb.name}</option>
            {/each}
        </select>
    </label>
    
    <label>
        Top K Results
        <input type="number" bind:value={topK} min="1" max="10" />
    </label>
{/if}
```

### How RAG Works in Chat

When student sends message to RAG-enabled assistant:

1. User message: "What is machine learning?"
2. Backend queries linked Knowledge Bases
3. Top K relevant chunks retrieved
4. Context injected into system prompt
5. LLM generates response with context
6. Response includes citations (optional)

See `backend_completions_pipeline.md` for technical flow.

---

## Document Processing

### Chunk Metadata

Each document chunk stores:

```json
{
  "source": "lecture1.pdf",
  "page": 3,
  "chunk_index": 5,
  "user_email": "prof@university.edu",
  "organization": "cs_department",
  "upload_date": 1678886400
}
```

### Chunking Strategy

- **Default Chunk Size:** 500 characters
- **Overlap:** 50 characters
- **Method:** Recursive text splitting
- **Preserves:** Paragraphs, code blocks

### Embedding Model

- **Default:** `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimension:** 384
- **Speed:** Fast inference, good quality

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Collection name exists" | Duplicate name | Choose different name |
| "Unsupported file type" | Invalid format | Use PDF, DOCX, MD, TXT, JSON |
| "File too large" | Exceeds limit | Split into smaller files |
| "Processing failed" | Corrupt document | Try different file |
| "Collection not found" | Invalid ID | Refresh list |

### User Feedback

```svelte
<script>
    let uploadErrors = [];
    
    async function uploadWithFeedback(file) {
        try {
            await knowledgeBaseService.uploadDocument(token, collectionId, file);
            return { success: true, file: file.name };
        } catch (error) {
            uploadErrors = [...uploadErrors, {
                file: file.name,
                error: error.response?.data?.detail || error.message
            }];
            return { success: false, file: file.name };
        }
    }
</script>

{#if uploadErrors.length > 0}
    <div class="alert alert-error">
        <p>Some files failed to upload:</p>
        <ul>
            {#each uploadErrors as err}
                <li>{err.file}: {err.error}</li>
            {/each}
        </ul>
    </div>
{/if}
```

---

## Best Practices

### Collection Organization

- **One collection per course/topic**
- **Clear, descriptive names**
- **Use descriptions to document content**

### Document Preparation

- **Clean formatting** - Remove headers/footers
- **Text-based PDFs** - Scanned documents need OCR
- **Structured content** - Better retrieval results

### Query Testing

- **Test before linking** - Verify collection has good coverage
- **Adjust Top K** - More results = more context, but slower
- **Check relevance** - Ensure retrieved chunks are actually relevant

---

## Performance Considerations

### Upload Speed

- **Large files:** May take several minutes
- **Batch uploads:** Process sequentially
- **Progress feedback:** Show per-file status

### Query Speed

- **Collection size:** Larger collections = slower queries
- **Top K:** Higher values = more computation
- **Typical:** 200-500ms per query

### Storage

- **Vectors:** ~1.5KB per chunk
- **Metadata:** ~0.5KB per chunk
- **Estimate:** 1000-page textbook ≈ 50MB vectors

---

## Related Documentation

- **Frontend Architecture:** `frontend_architecture.md`
- **Backend KB Integration:** `backend_knowledge_base.md`
- **RAG in Completions:** `backend_completions_pipeline.md`
- **Assistant Management:** `frontend_assistants_management.md`

