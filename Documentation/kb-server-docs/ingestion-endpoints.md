# Ingestion Endpoints

This document describes the main ingestion-related API endpoints in the Lamb KB Server, including their purpose, workflow, and differences.

---

## 1. `/collections/{collection_id}/ingest`
**Purpose:** Process a previously uploaded file using a specified ingestion plugin, but does not add the processed documents to the collection yet.

- **Method:** POST
- **Request:** JSON body specifying the file path, plugin name, and plugin parameters.
- **Response:** Returns processed document chunks and metadata.
- **Use Case:** Preview, test, or validate file processing before committing to a collection.

---

## 2. `/collections/{collection_id}/ingest-file`
**Purpose:** Upload, process, and add a file to a collection in one operation.

- **Method:** POST
- **Request:** Multipart/form-data with file upload, plugin name, and parameters.
- **Response:** Adds resulting document chunks to the collection and returns status.
- **Use Case:** Main workflow for ingesting new content into a knowledge base collection.

---

## 3. `/collections/{collection_id}/ingest-url`
**Purpose:** Fetch, process, and add content from URLs directly into a collection in one operation.

- **Method:** POST
- **Request:** JSON body specifying a list of URLs and plugin parameters.
- **Workflow:**
    1. The server fetches content from the provided URLs using the `url_ingest` plugin (which uses Firecrawl).
    2. The content is processed (converted to Markdown, chunked, and metadata extracted).
    3. The resulting document chunks are added directly to the specified collection.
- **Response:** Status and document count.
- **Use Case:** Bulk ingesting web content or documents from the internet into a collection.

---

## Summary Table

| Endpoint       | Upload | Processing | Adds to Collection | Input Type           | Use Case                |
|----------------|--------|------------|--------------------|----------------------|-------------------------|
| `/ingest`      | No     | Yes        | No                 | Uploaded File        | Preview/Test/Validate   |
| `/ingest-file` | Yes    | Yes        | Yes                | File Upload          | Full Ingestion Workflow |
| `/ingest-url`  | No     | Yes        | Yes                | URLs (web content)   | Bulk Web Ingestion      |

---

## Example Usage

### `/ingest`
```bash
curl -X POST 'http://localhost:9090/collections/1/ingest' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
        "file_path": "/path/to/uploaded/file.txt",
        "plugin_name": "simple_ingest",
        "plugin_params": {"chunk_size": 1000}
      }'
```

### `/ingest-file`
```bash
curl -X POST 'http://localhost:9090/collections/1/ingest-file' \
  -H 'Authorization: Bearer <token>' \
  -F 'file=@/path/to/document.txt' \
  -F 'plugin_name=simple_ingest' \
  -F 'plugin_params={"chunk_size": 1000}'
```

### `/ingest-url`
```bash
curl -X POST 'http://localhost:9090/collections/1/ingest-url' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
        "urls": ["https://example.com/page1", "https://example.com/page2"],
        "plugin_params": {"chunk_size": 1000}
      }'
```

---

The `/ingestion/plugins` informs the available endpoints:
{
  "plugins": [
    {
      "name": "markitdown_ingest",
      "description": "Ingest various file formats by converting to Markdown using MarkItDown with configurable chunking",
      "kind": "file-ingest",
      "supported_file_types": [
        "html", "json", "mp3", "zip", "epub", "pptx", "xml", "pdf",
        "docx", "xlsx", "wav", "xls", "csv"
      ],
      "parameters": {
        "chunk_size": {
          "type": "integer",
          "description": "Size of each chunk",
          "default": 1000,
          "required": false,
          "enum": null
        },
        "chunk_unit": {
          "type": "string",
          "description": "Unit for chunking (char, word, line)",
          "default": "char",
          "required": false,
          "enum": ["char", "word", "line"]
        },
        "chunk_overlap": {
          "type": "integer",
          "description": "Number of units to overlap between chunks",
          "default": 200,
          "required": false,
          "enum": null
        }
      }
    },
    {
      "name": "simple_ingest",
      "description": "Ingest text files with configurable chunking options",
      "kind": "file-ingest",
      "supported_file_types": [
        "*.txt", "*.md"
      ],
      "parameters": {
        "chunk_size": {
          "type": "integer",
          "description": "Size of each chunk",
          "default": 1000,
          "required": false,
          "enum": null
        },
        "chunk_unit": {
          "type": "string",
          "description": "Unit for chunking (char, word, line)",
          "default": "char",
          "required": false,
          "enum": ["char", "word", "line"]
        },
        "chunk_overlap": {
          "type": "integer",
          "description": "Number of units to overlap between chunks",
          "default": 200,
          "required": false,
          "enum": null
        }
      }
    },
    {
      "name": "url_ingest",
      "description": "Ingest web pages from URLs using Firecrawl",
      "kind": "base-ingest",
      "supported_file_types": [
        "url"
      ],
      "parameters": {
        "chunk_size": {
          "type": "integer",
          "description": "Size of each chunk",
          "default": 1000,
          "required": false,
          "enum": null
        },
        "chunk_unit": {
          "type": "string",
          "description": "Unit for chunking (char, word, line)",
          "default": "char",
          "required": false,
          "enum": ["char", "word", "line"]
        },
        "chunk_overlap": {
          "type": "integer",
          "description": "Number of units to overlap between chunks",
          "default": 200,
          "required": false,
          "enum": null
        },
        "urls": {
          "type": "array",
          "description": "List of URLs to ingest",
          "default": null,
          "required": true,
          "enum": null
        }
      }
    }
  ]
}

