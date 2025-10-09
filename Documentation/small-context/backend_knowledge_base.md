# Backend: Knowledge Base Integration

**Purpose:** Document processing, vector storage, and RAG integration with KB server  
**Related Docs:** `backend_completions_pipeline.md`, `frontend_kb_management.md`, `backend_architecture.md`

---

## Overview

LAMB integrates with a Knowledge Base (KB) Server for document processing and semantic search:
- **Document ingestion** - PDF, Word, Markdown, TXT, JSON
- **Text extraction and chunking** - Split documents into semantic chunks
- **Vector embeddings** - Sentence-transformers for semantic search
- **ChromaDB storage** - Persistent vector database
- **RAG integration** - Retrieve context during completions

---

## Architecture

```
┌──────────────┐                 ┌──────────────────┐
│              │  1. Create      │                  │
│   Frontend   │  Collection     │   LAMB Backend   │
│              ├────────────────►│  Creator         │
└──────────────┘                 │  Interface       │
                                 └────────┬─────────┘
                                          │
                                          │ 2. Forward request
                                          │    with user/org info
                                          ▼
                                 ┌──────────────────┐
                                 │                  │
                                 │  KB Server       │
                                 │  :9090           │
                                 │                  │
                                 └────────┬─────────┘
                                          │
                                          │ 3. Store in ChromaDB
                                          ▼
                                 ┌──────────────────┐
                                 │   ChromaDB       │
                                 │   Collections    │
                                 │   + Vectors      │
                                 └──────────────────┘
```

**Key Points:**
- LAMB doesn't process documents directly
- KB Server is independent microservice
- LAMB forwards requests with user/org context
- ChromaDB stores vectors and metadata

---

## KB Server Configuration

### Organization-Specific Config

Each organization can have its own KB server:

```json
{
  "kb_server": {
    "url": "http://localhost:9090",
    "api_key": "kb-api-key-for-org"
  }
}
```

**Fallback to Environment Variables:**

```bash
KB_SERVER_URL=http://localhost:9090
KB_API_KEY=kb-api-key
```

### Resolution in Code

```python
from backend.lamb.completions.org_config_resolver import OrganizationConfigResolver

config_resolver = OrganizationConfigResolver(user_email)
kb_config = config_resolver.get_kb_server_config()

kb_server_url = kb_config.get("url")
kb_api_key = kb_config.get("api_key")
```

---

## Collection Management

### Create Collection

**Endpoint:** `POST /creator/knowledgebases/create`

**File:** `/backend/creator_interface/knowledges_router.py`

```python
@router.post("/knowledgebases/create")
async def create_knowledgebase(request: CreateKBRequest, http_request: Request):
    """
    Create new Knowledge Base collection
    
    Args:
        request: {
            collection_name: "CS101 Lectures",
            description: "Computer Science 101 materials"
        }
    """
    # Get user
    creator_user = get_creator_user_from_token(http_request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get organization
    db_manager = LambDatabaseManager()
    org = db_manager.get_user_organization(creator_user['id'])
    org_slug = org['slug'] if org else 'lamb'
    
    # Get KB server config
    config_resolver = OrganizationConfigResolver(creator_user['email'])
    kb_config = config_resolver.get_kb_server_config()
    
    kb_server_url = kb_config.get("url")
    kb_api_key = kb_config.get("api_key")
    
    # Forward to KB server
    kb_manager = KBServerManager(kb_server_url, kb_api_key)
    result = await kb_manager.create_collection(
        collection_name=request.collection_name,
        description=request.description,
        user_email=creator_user['email'],
        organization_slug=org_slug
    )
    
    return result
```

**KB Server Request:**

```http
POST http://kb-server:9090/api/collection
Authorization: Bearer kb-api-key
Content-Type: application/json

{
  "name": "CS101 Lectures",
  "description": "Computer Science 101 materials",
  "metadata": {
    "user_email": "prof@university.edu",
    "organization": "engineering"
  }
}
```

**KB Server Response:**

```json
{
  "id": "collection-uuid",
  "name": "CS101 Lectures",
  "description": "Computer Science 101 materials",
  "created_at": 1678886400
}
```

---

### List Collections

**Endpoint:** `GET /creator/knowledgebases/list`

```python
@router.get("/knowledgebases/list")
async def list_knowledgebases(http_request: Request):
    """
    List user's Knowledge Base collections
    """
    creator_user = get_creator_user_from_token(http_request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get KB server config
    config_resolver = OrganizationConfigResolver(creator_user['email'])
    kb_config = config_resolver.get_kb_server_config()
    
    kb_server_url = kb_config.get("url")
    kb_api_key = kb_config.get("api_key")
    
    # Get user's organization
    db_manager = LambDatabaseManager()
    org = db_manager.get_user_organization(creator_user['id'])
    org_slug = org['slug'] if org else 'lamb'
    
    # Query KB server
    kb_manager = KBServerManager(kb_server_url, kb_api_key)
    collections = await kb_manager.list_collections(
        user_email=creator_user['email'],
        organization_slug=org_slug
    )
    
    return {"collections": collections}
```

---

### Get Collection Details

**Endpoint:** `GET /creator/knowledgebases/{collection_id}`

```python
@router.get("/knowledgebases/{collection_id}")
async def get_knowledgebase(collection_id: str, http_request: Request):
    """
    Get collection details including document list
    """
    creator_user = get_creator_user_from_token(http_request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    config_resolver = OrganizationConfigResolver(creator_user['email'])
    kb_config = config_resolver.get_kb_server_config()
    
    kb_server_url = kb_config.get("url")
    kb_api_key = kb_config.get("api_key")
    
    kb_manager = KBServerManager(kb_server_url, kb_api_key)
    collection = await kb_manager.get_collection(collection_id)
    
    return collection
```

---

### Upload Document

**Endpoint:** `POST /creator/knowledgebases/{collection_id}/upload`

```python
@router.post("/knowledgebases/{collection_id}/upload")
async def upload_document(
    collection_id: str,
    file: UploadFile,
    http_request: Request
):
    """
    Upload document to collection
    
    Supported formats: PDF, DOCX, MD, TXT, JSON
    """
    creator_user = get_creator_user_from_token(http_request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.md', '.txt', '.json']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}"
        )
    
    # Get KB server config
    config_resolver = OrganizationConfigResolver(creator_user['email'])
    kb_config = config_resolver.get_kb_server_config()
    
    kb_server_url = kb_config.get("url")
    kb_api_key = kb_config.get("api_key")
    
    # Read file content
    content = await file.read()
    
    # Forward to KB server
    kb_manager = KBServerManager(kb_server_url, kb_api_key)
    result = await kb_manager.upload_document(
        collection_id=collection_id,
        filename=file.filename,
        content=content
    )
    
    return result
```

**KB Server Processing:**

1. Receive file
2. Extract text based on format:
   - PDF: pypdf or pdfplumber
   - DOCX: python-docx
   - MD/TXT: direct read
   - JSON: parse and extract text fields
3. Split into chunks (500 chars, 50 overlap)
4. Generate embeddings (sentence-transformers)
5. Store in ChromaDB with metadata

---

### Query Collection

**Endpoint:** `GET /creator/knowledgebases/{collection_id}/query`

```python
@router.get("/knowledgebases/{collection_id}/query")
async def query_knowledgebase(
    collection_id: str,
    q: str,
    top_k: int = 5,
    http_request: Request = None
):
    """
    Semantic search in collection
    
    Args:
        q: Query text
        top_k: Number of results to return
    """
    creator_user = get_creator_user_from_token(http_request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    config_resolver = OrganizationConfigResolver(creator_user['email'])
    kb_config = config_resolver.get_kb_server_config()
    
    kb_server_url = kb_config.get("url")
    kb_api_key = kb_config.get("api_key")
    
    kb_manager = KBServerManager(kb_server_url, kb_api_key)
    results = await kb_manager.query_collection(
        collection_id=collection_id,
        query=q,
        top_k=top_k
    )
    
    return results
```

**KB Server Response:**

```json
{
  "results": [
    {
      "text": "Machine learning is a subset of artificial intelligence...",
      "metadata": {
        "source": "lecture1.pdf",
        "page": 3,
        "chunk_index": 5,
        "user_email": "prof@university.edu",
        "organization": "engineering"
      },
      "distance": 0.234
    },
    {
      "text": "Neural networks are computing systems inspired by...",
      "metadata": {
        "source": "lecture2.pdf",
        "page": 1,
        "chunk_index": 2,
        "user_email": "prof@university.edu",
        "organization": "engineering"
      },
      "distance": 0.456
    }
  ]
}
```

---

### Delete Collection

**Endpoint:** `DELETE /creator/knowledgebases/{collection_id}`

```python
@router.delete("/knowledgebases/{collection_id}")
async def delete_knowledgebase(collection_id: str, http_request: Request):
    """
    Delete collection and all documents
    """
    creator_user = get_creator_user_from_token(http_request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    config_resolver = OrganizationConfigResolver(creator_user['email'])
    kb_config = config_resolver.get_kb_server_config()
    
    kb_server_url = kb_config.get("url")
    kb_api_key = kb_config.get("api_key")
    
    kb_manager = KBServerManager(kb_server_url, kb_api_key)
    result = await kb_manager.delete_collection(collection_id)
    
    return result
```

---

## KBServerManager Helper

**File:** `/backend/creator_interface/kb_server_manager.py`

```python
import httpx

class KBServerManager:
    """
    Helper class for KB Server operations
    """
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
    
    async def create_collection(
        self,
        collection_name: str,
        description: str,
        user_email: str,
        organization_slug: str
    ):
        """Create new collection"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/collection",
                json={
                    "name": collection_name,
                    "description": description,
                    "metadata": {
                        "user_email": user_email,
                        "organization": organization_slug
                    }
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def list_collections(self, user_email: str, organization_slug: str):
        """List user's collections"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/collections",
                params={
                    "user_email": user_email,
                    "organization": organization_slug
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def upload_document(
        self,
        collection_id: str,
        filename: str,
        content: bytes
    ):
        """Upload document to collection"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            files = {"file": (filename, content)}
            response = await client.post(
                f"{self.base_url}/api/collection/{collection_id}/upload",
                files=files,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def query_collection(
        self,
        collection_id: str,
        query: str,
        top_k: int = 5
    ):
        """Query collection for relevant chunks"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/collection/{collection_id}/query",
                json={"query": query, "top_k": top_k},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_collection(self, collection_id: str):
        """Delete collection"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/collection/{collection_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
```

---

## RAG Integration in Completions

### Simple RAG Processor

**File:** `/backend/lamb/completions/rag/simple_rag.py`

```python
def rag_processor(messages: List[Dict], assistant: Assistant = None):
    """
    Query Knowledge Base and format context
    
    Args:
        messages: Conversation messages
        assistant: Assistant configuration
    
    Returns:
        {
            "context": "formatted context text",
            "sources": [{"index": 1, "source": "file.pdf", "page": 3}]
        }
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
    
    if not kb_server_url:
        logger.error("KB server URL not configured")
        return {"context": "", "sources": []}
    
    # Parse collections (comma-separated)
    collections = [c.strip() for c in assistant.RAG_collections.split(',') if c.strip()]
    top_k = getattr(assistant, 'RAG_Top_k', 3)
    
    # Query each collection
    all_results = []
    for collection_id in collections:
        try:
            response = requests.post(
                f"{kb_server_url}/api/collection/{collection_id}/query",
                json={"query": last_user_message, "top_k": top_k},
                headers={"Authorization": f"Bearer {kb_api_key}"},
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                all_results.extend(data.get("results", []))
            else:
                logger.error(f"RAG query failed for {collection_id}: {response.status_code}")
        except Exception as e:
            logger.error(f"RAG query exception for {collection_id}: {e}")
    
    if not all_results:
        return {"context": "", "sources": []}
    
    # Format context
    context_parts = []
    sources = []
    
    for i, result in enumerate(all_results):
        context_parts.append(f"[{i+1}] {result['text']}")
        sources.append({
            "index": i+1,
            "source": result.get('metadata', {}).get('source', 'Unknown'),
            "page": result.get('metadata', {}).get('page', 'N/A'),
            "distance": result.get('distance', 0.0)
        })
    
    context = "\n\n".join(context_parts)
    
    return {
        "context": context,
        "sources": sources
    }
```

**Usage in Prompt Processor:**

```python
def prompt_processor(request, assistant=None, rag_context=None):
    messages = []
    
    if assistant and assistant.system_prompt:
        system_content = assistant.system_prompt
        
        # Inject RAG context
        if rag_context and rag_context.get("context"):
            system_content += f"\n\nRelevant information:\n{rag_context['context']}"
        
        messages.append({"role": "system", "content": system_content})
    
    # Add user messages...
    return messages
```

---

## Document Processing Details

### Supported Formats

| Format | Extensions | Library | Notes |
|--------|-----------|---------|-------|
| PDF | `.pdf` | pypdf, pdfplumber | Text-based PDFs only (no OCR) |
| Word | `.docx` | python-docx | Modern Word format only |
| Markdown | `.md` | Built-in | Preserves structure |
| Text | `.txt` | Built-in | Plain text |
| JSON | `.json` | Built-in | Extracts text fields |

### Chunking Strategy

**Default Settings:**
- **Chunk Size:** 500 characters
- **Overlap:** 50 characters
- **Method:** Recursive text splitting

**Algorithm:**
1. Split on paragraph breaks first
2. If paragraph > chunk size, split on sentences
3. If sentence > chunk size, split on words
4. Always maintain overlap between chunks

### Embeddings

**Model:** `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimension:** 384
- **Speed:** ~1000 sentences/second on CPU
- **Quality:** Good for general text

**Alternative Models:**
- `all-mpnet-base-v2` - Better quality, slower
- `paraphrase-multilingual` - For multilingual content

---

## ChromaDB Storage

### Collection Structure

**Collection Naming:**
```
{organization_slug}_{user_email}_{collection_name}
```

Example: `engineering_prof@university.edu_CS101_Lectures`

### Document Metadata

Each chunk stores:
```python
{
    "source": "lecture1.pdf",
    "page": 3,
    "chunk_index": 5,
    "user_email": "prof@university.edu",
    "organization": "engineering",
    "upload_date": 1678886400
}
```

### Query Metadata Filtering

```python
collection.query(
    query_texts=["machine learning"],
    n_results=5,
    where={
        "user_email": "prof@university.edu",
        "organization": "engineering"
    }
)
```

---

## Performance Considerations

### Upload Speed

- **PDF:** 1-5 pages/second
- **DOCX:** 2-10 pages/second
- **Large files:** May take several minutes

**Optimization:**
- Process asynchronously
- Show progress to user
- Limit file size (e.g., 50MB max)

### Query Speed

- **Collection size:** Larger = slower
- **Top K:** Higher = more results = slower
- **Typical:** 200-500ms per collection

**Optimization:**
- Limit collections per assistant
- Use reasonable Top K (3-5)
- Cache frequent queries (future)

### Storage

**Estimates:**
- **Vectors:** ~1.5KB per chunk
- **Metadata:** ~0.5KB per chunk
- **Total:** ~2KB per chunk

**Example:** 1000-page textbook ≈ 10,000 chunks ≈ 20MB

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "KB server unreachable" | Server down/wrong URL | Check KB server status |
| "Unsupported file type" | Invalid format | Use supported formats |
| "File too large" | Exceeds limit | Split into smaller files |
| "Processing failed" | Corrupt document | Try different file |
| "Collection not found" | Invalid ID | Verify collection exists |
| "No results" | Empty collection | Upload documents first |

### Error Response Format

```json
{
  "detail": "Error message"
}
```

---

## Related Documentation

- **Backend Completions:** `backend_completions_pipeline.md`
- **Frontend KB Management:** `frontend_kb_management.md`
- **Backend Architecture:** `backend_architecture.md`
- **Organizations:** `backend_organizations.md`

