#!/usr/bin/env python3
"""
YouTube Video Transcript Ingestion Script

This script extracts subtitles from YouTube videos and generates JSON files
in the format compatible with the knowledge base system.
"""

import json
import logging
import sys
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import re

# Import the YouTube loader from the plugins directory
from plugins.youtube import YoutubeLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def parse_youtube_url(url: str) -> Optional[str]:
    """Extract video ID from a YouTube URL."""
    parsed = urlparse(url)
    
    if parsed.netloc in ['youtu.be']:
        return parsed.path[1:]
    elif parsed.netloc in ['youtube.com', 'www.youtube.com', 'm.youtube.com']:
        if parsed.path == '/watch':
            query_params = parse_qs(parsed.query)
            return query_params.get('v', [None])[0]
        elif parsed.path.startswith('/embed/'):
            return parsed.path.split('/embed/')[1]
    return None


def seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to timestamp format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def clean_text(text: str) -> str:
    """Clean and normalize transcript text."""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common transcription artifacts
    text = re.sub(r'\[.*?\]', '', text)  # Remove [Music], [Applause], etc.
    text = re.sub(r'\(.*?\)', '', text)  # Remove (inaudible), etc.
    
    # Clean up punctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)  # Fix spacing before punctuation
    text = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', text)  # Ensure space after sentence endings
    
    return text.strip()


def chunk_transcript(transcript_pieces: List[Dict], chunk_duration: float = 60.0) -> List[Dict]:
    """
    Chunk transcript pieces into larger segments based on duration.
    
    Args:
        transcript_pieces: List of transcript pieces with start, duration, and text
        chunk_duration: Target duration for each chunk in seconds
    
    Returns:
        List of chunked transcript segments
    """
    chunks = []
    current_chunk = {
        'start': 0,
        'end': 0,
        'text_parts': [],
        'original_text_parts': []
    }
    
    for piece in transcript_pieces:
        piece_start = piece['start']
        piece_end = piece['start'] + piece['duration']
        piece_text = clean_text(piece['text'])
        
        # Skip empty pieces
        if not piece_text:
            continue
            
        # Start new chunk if this is the first piece
        if not current_chunk['text_parts']:
            current_chunk['start'] = piece_start
        
        # Add piece to current chunk
        current_chunk['text_parts'].append(piece_text)
        current_chunk['original_text_parts'].append(piece['text'])
        current_chunk['end'] = piece_end
        
        # Check if we should start a new chunk
        chunk_duration_so_far = current_chunk['end'] - current_chunk['start']
        
        if chunk_duration_so_far >= chunk_duration:
            # Finalize current chunk
            if current_chunk['text_parts']:
                chunks.append(current_chunk)
            
            # Start new chunk
            current_chunk = {
                'start': 0,
                'end': 0, 
                'text_parts': [],
                'original_text_parts': []
            }
    
    # Add final chunk if it has content
    if current_chunk['text_parts']:
        chunks.append(current_chunk)
    
    return chunks


def generate_json_output(video_id: str, video_url: str, chunks: List[Dict], 
                        filename: str, file_number: str = "1") -> List[Dict]:
    """Generate JSON output in the required format."""
    json_output = []
    
    for i, chunk in enumerate(chunks, 1):
        # Combine text parts
        cleaned_text = ' '.join(chunk['text_parts'])
        original_text = ' '.join(chunk['original_text_parts'])
        
        # Generate timestamp strings
        timestamp_start = seconds_to_timestamp(chunk['start'])
        timestamp_end = seconds_to_timestamp(chunk['end'])
        
        # Generate URL with timestamp
        url_with_timestamp = f"{video_url}&t={int(chunk['start'])}s"
        
        entry = {
            "number": i,
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "text": cleaned_text,
            "old_text": original_text,
            "kind": "online_video",
            "file_number": file_number,
            "filename": filename,
            "url": url_with_timestamp
        }
        
        json_output.append(entry)
    
    return json_output


def main():
    parser = argparse.ArgumentParser(description='Extract YouTube video transcripts and generate JSON')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('-o', '--output', help='Output JSON file path', default=None)
    parser.add_argument('-c', '--chunk-duration', type=float, default=60.0, 
                       help='Target chunk duration in seconds (default: 60)')
    parser.add_argument('-l', '--language', default='en', 
                       help='Preferred subtitle language (default: en)')
    parser.add_argument('-f', '--file-number', default='1', 
                       help='File number for JSON output (default: 1)')
    parser.add_argument('--proxy', help='Proxy URL for yt-dlp')
    
    args = parser.parse_args()
    
    # Extract video ID from URL
    video_id = parse_youtube_url(args.url)
    if not video_id:
        log.error(f"Could not extract video ID from URL: {args.url}")
        sys.exit(1)
    
    log.info(f"Processing video ID: {video_id}")
    
    # Load transcript using the YouTube loader
    try:
        loader = YoutubeLoader(
            video_id=video_id,
            language=args.language,
            proxy_url=args.proxy
        )
        
        documents = loader.load()
        if not documents:
            log.error("No transcript found for the video")
            sys.exit(1)
            
        doc = documents[0]
        transcript_map = doc.metadata.get('timestamp_map', [])
        
        if not transcript_map:
            log.error("No timestamp mapping found in transcript")
            sys.exit(1)
            
        log.info(f"Loaded transcript with {len(transcript_map)} segments")
        
    except Exception as e:
        log.error(f"Error loading transcript: {e}")
        sys.exit(1)
    
    # Convert timestamp map to transcript pieces format
    transcript_pieces = []
    full_text = doc.page_content
    
    for segment in transcript_map:
        text = full_text[segment['start']:segment['end']].strip()
        transcript_pieces.append({
            'start': segment['time'],
            'duration': segment['duration'],
            'text': text
        })
    
    # Chunk the transcript
    log.info(f"Chunking transcript with target duration: {args.chunk_duration} seconds")
    chunks = chunk_transcript(transcript_pieces, args.chunk_duration)
    log.info(f"Generated {len(chunks)} chunks")
    
    # Generate filename
    video_title = doc.metadata.get('title', f'video_{video_id}')
    # Clean title for filename
    safe_title = re.sub(r'[^\w\s-]', '', video_title)
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    filename = f"{safe_title}.json"
    
    # Generate JSON output
    json_output = generate_json_output(
        video_id=video_id,
        video_url=args.url,
        chunks=chunks,
        filename=filename,
        file_number=args.file_number
    )
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"{safe_title}_transcript.json")
    
    # Write JSON file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        
        log.info(f"Successfully wrote transcript to: {output_path}")
        log.info(f"Generated {len(json_output)} transcript segments")
        
        # Print summary
        total_duration = chunks[-1]['end'] - chunks[0]['start'] if chunks else 0
        print(f"\nSummary:")
        print(f"Video ID: {video_id}")
        print(f"Title: {video_title}")
        print(f"Total duration: {total_duration:.1f} seconds")
        print(f"Number of chunks: {len(json_output)}")
        print(f"Output file: {output_path}")
        
    except Exception as e:
        log.error(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()