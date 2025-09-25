# YouTube Video Transcript Ingestion Tool

This tool extracts subtitles from YouTube videos and generates JSON files compatible with the knowledge base system format.

## Features

- Extracts subtitles from YouTube videos using yt-dlp
- Automatically chunks transcripts into configurable time segments
- Generates timestamped URLs for each chunk
- Cleans and normalizes transcript text
- Outputs JSON in the knowledge base system format
- Supports multiple subtitle languages
- Includes proxy support for restricted networks

## Installation

### Prerequisites

Make sure you have Python 3.7+ installed.

### Install Dependencies

```bash
# Install required Python packages
pip install -r plugins/requirements.txt
```

The main dependencies are:
- `yt-dlp` - For extracting YouTube video information and subtitles
- `langchain-core` - For document processing
- `requests` - For HTTP requests

## Usage

### Basic Usage

```bash
python ingest-youtube.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Advanced Options

```bash
python ingest-youtube.py [URL] [OPTIONS]

Arguments:
  url                   YouTube video URL (required)

Options:
  -o, --output OUTPUT   Output JSON file path (default: auto-generated)
  -c, --chunk-duration  Target chunk duration in seconds (default: 60)
  -l, --language       Preferred subtitle language (default: en)
  -f, --file-number    File number for JSON output (default: 1)
  --proxy PROXY        Proxy URL for yt-dlp
  -h, --help           Show help message
```

### Examples

1. **Basic extraction with 60-second chunks:**
   ```bash
   python ingest-youtube.py "https://www.youtube.com/watch?v=cwHmVpLOqas"
   ```

2. **Custom output file and chunk duration:**
   ```bash
   python ingest-youtube.py "https://www.youtube.com/watch?v=cwHmVpLOqas" \
     -o my_video_transcript.json \
     -c 45
   ```

3. **Spanish subtitles with specific file number:**
   ```bash
   python ingest-youtube.py "https://www.youtube.com/watch?v=cwHmVpLOqas" \
     -l es \
     -f "42"
   ```

4. **Using a proxy:**
   ```bash
   python ingest-youtube.py "https://www.youtube.com/watch?v=cwHmVpLOqas" \
     --proxy "http://proxy.example.com:8080"
   ```

## Output Format

The script generates JSON files with the following structure:

```json
[
  {
    "number": 1,
    "timestamp_start": "00:00:03,770",
    "timestamp_end": "00:01:04,390",
    "text": "Cleaned and processed transcript text...",
    "old_text": "Original raw transcript text...",
    "kind": "online_video",
    "file_number": "37",
    "filename": "Video-Title.json",
    "url": "https://www.youtube.com/watch?v=VIDEO_ID&t=3s"
  }
]
```

### Field Descriptions

- `number`: Sequential chunk number
- `timestamp_start`: Start time in HH:MM:SS,mmm format
- `timestamp_end`: End time in HH:MM:SS,mmm format  
- `text`: Cleaned and processed transcript text
- `old_text`: Original raw transcript text
- `kind`: Always "online_video" for YouTube content
- `file_number`: User-specified file number for organization
- `filename`: Generated filename based on video title
- `url`: YouTube URL with timestamp pointing to chunk start

## Text Processing

The script performs several text cleaning operations:

1. **Normalization**: Removes extra whitespace and normalizes formatting
2. **Artifact Removal**: Removes common transcription artifacts like [Music], [Applause], (inaudible)
3. **Punctuation Cleanup**: Fixes spacing around punctuation marks
4. **Sentence Boundaries**: Ensures proper spacing after sentence endings

## Supported YouTube URLs

The script supports various YouTube URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube-nocookie.com/watch?v=VIDEO_ID`

## Troubleshooting

### Common Issues

1. **"No transcript found"**: The video may not have subtitles available
2. **"ModuleNotFoundError"**: Install dependencies with `pip install -r plugins/requirements.txt`
3. **Network errors**: Try using the `--proxy` option if behind a firewall

### Subtitle Language Support

The script will attempt to find subtitles in the specified language. If not found, it will fall back to the first available language. Common language codes:

- `en` - English
- `es` - Spanish  
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese

### Performance Notes

- Processing time depends on video length and subtitle availability
- Longer videos will generate more chunks and take more time
- Network speed affects subtitle download time

## API Key Configuration (Optional)

For better video metadata (titles), you can set a YouTube Data API key:

```bash
export YOUTUBE_API_KEY="your_api_key_here"
```

This is optional - the script will fall back to web scraping for titles if no API key is provided.

## Integration with Knowledge Base

The generated JSON files can be directly ingested into the ChromaDB-based knowledge base system for:

- Semantic search across video content
- Question answering based on video transcripts
- Content recommendation and discovery
- Educational content analysis

## License

This tool is part of the LAMB project and follows the same licensing terms.