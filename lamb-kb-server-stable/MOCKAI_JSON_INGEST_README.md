# MockAI JSON Ingest Plugin

## Overview

The `mockai-json-ingest` plugin is designed to handle structured JSON data files and ZIP archives containing multiple JSON files. It preserves all metadata from the JSON structure while creating searchable text chunks for the knowledge base.

## Features

- **Full Metadata Preservation**: Extracts and stores all fields from JSON objects as metadata
- **Structure-Aware Chunking**: Intelligently splits text content while preserving logical boundaries
- **ZIP File Support**: Processes ZIP archives containing multiple JSON files in batch
- **Flexible Configuration**: Configurable chunk sizes, overlap, and metadata extraction options
- **Error Handling**: Robust error handling for malformed JSON and ZIP files

## Supported File Types

- `.json` - Individual JSON files
- `.zip` - ZIP archives containing JSON files

## JSON Data Format

The plugin expects JSON data in the following format:

```json
[
    {
        "number": 1,
        "title": "Document Title",
        "page": 1,
        "text": "Main content text to be chunked...",
        "kind": "online_pdf",
        "filename": "document.pdf",
        "url": "https://example.com/document.pdf",
        "timestamp_start": "00:00:00",
        "timestamp_end": "00:01:30",
        // ... any additional metadata fields
    }
]
```

## Configuration Parameters

### Required Parameters
- None (all parameters have defaults)

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | integer | 2000 | Size of each text chunk in characters (100-10000) |
| `chunk_overlap` | integer | 200 | Characters to overlap between chunks (0-1000) |

## Usage Examples

### Processing Individual JSON Files

```bash
# Basic usage with defaults
curl -X POST 'http://localhost:9090/collections/1/ingest-file' \
  -H 'Authorization: Bearer 0p3n-w3bu!' \
  -F 'file=@/path/to/data.json' \
  -F 'plugin_name=mockai_json_ingest'

# With custom chunking parameters
curl -X POST 'http://localhost:9090/collections/1/ingest-file' \
  -H 'Authorization: Bearer 0p3n-w3bu!' \
  -F 'file=@/path/to/data.json' \
  -F 'plugin_name=mockai_json_ingest' \
  -F 'plugin_params={"chunk_size": 1500, "chunk_overlap": 300}'
```

### Processing ZIP Files

```bash
# Process ZIP file containing multiple JSON files
curl -X POST 'http://localhost:9090/collections/1/ingest-file' \
  -H 'Authorization: Bearer 0p3n-w3bu!' \
  -F 'file=@/path/to/data-collection.zip' \
  -F 'plugin_name=mockai_json_ingest' \
  -F 'plugin_params={"chunk_size": 1000}'
```

### Direct API Usage

```bash
# Using the direct ingest endpoint
curl -X POST 'http://localhost:9090/collections/1/ingest-base' \
  -H 'Authorization: Bearer 0p3n-w3bu!' \
  -H 'Content-Type: application/json' \
  -d '{
    "plugin_name": "mockai_json_ingest",
    "plugin_params": {
      "chunk_size": 2000,
      "chunk_overlap": 200
    }
  }'
```

## Metadata Extraction

The plugin extracts all fields from JSON objects and stores them as metadata:

### Preserved Fields
- All original JSON fields become metadata keys
- `text` field becomes the searchable content
- `old_text` fields are prefixed with `original_`
- Nested objects are flattened (e.g., `config.version` becomes `config_version`)

### Added Metadata
- `source_file`: Original filename
- `ingestion_plugin`: Plugin name ("mockai_json_ingest")
- `ingestion_timestamp`: Processing timestamp
- `chunking_strategy`: "mockai_json_structure"
- `plugin_version`: Plugin version

### Chunk Metadata
- `chunk_index`: Index of chunk within document
- `chunk_start`: Starting character position
- `chunk_end`: Ending character position
- `total_chunks`: Total number of chunks for the document

## Output Format

The plugin returns chunks in the standard format:

```json
[
    {
        "text": "Content of the text chunk...",
        "metadata": {
            "number": 1,
            "title": "Document Title",
            "kind": "online_pdf",
            "filename": "document.pdf",
            "source_file": "document.json",
            "ingestion_plugin": "mockai_json_ingest",
            "ingestion_timestamp": "2025-09-24T10:30:00.123456",
            "chunking_strategy": "mockai_json_structure",
            "plugin_version": "1.0.0",
            "chunk_index": 0,
            "chunk_start": 0,
            "chunk_end": 2000,
            "total_chunks": 3
        }
    }
]
```

## Error Handling

The plugin handles various error conditions:

- **Invalid JSON**: Returns error for malformed JSON files
- **Invalid ZIP**: Returns error for corrupted ZIP files
- **Missing Files**: Returns 404 for non-existent files
- **Parameter Validation**: Validates chunk size and overlap parameters
- **Memory Issues**: Handles large files gracefully

## Integration with LAMB KB Server

The plugin integrates seamlessly with the existing LAMB Knowledge Base Server:

1. **Plugin Discovery**: Automatically discovered via `discover_plugins()`
2. **File Registry**: Tracks processing status and metadata
3. **Background Processing**: Supports large file processing via background tasks
4. **ChromaDB Integration**: Stores chunks with full metadata in vector database
5. **API Endpoints**: Works with existing ingestion endpoints

## Use Cases

### Video Transcripts
- Process YouTube transcript JSON exports
- Preserve timestamps, video metadata, and speaker information
- Enable semantic search across video content

### PDF Documents
- Process extracted PDF content with page numbers
- Maintain document structure and metadata
- Support multi-page document chunking

### API Documentation
- Process API specification JSON files
- Preserve endpoint metadata, parameters, and examples
- Enable documentation search and discovery

### Research Data
- Process research datasets with metadata
- Preserve study information, timestamps, and context
- Support academic search and analysis

## Performance Considerations

- **Memory Usage**: Processes files in chunks to handle large datasets
- **Processing Speed**: Optimized JSON parsing and chunking algorithms
- **Scalability**: Supports batch processing of ZIP archives
- **Metadata Overhead**: Rich metadata increases storage requirements

## Security Notes

- **File Validation**: Validates JSON structure before processing
- **Path Safety**: Sanitizes file paths and names
- **Size Limits**: Respects system memory constraints
- **Error Isolation**: Prevents plugin errors from affecting other components
