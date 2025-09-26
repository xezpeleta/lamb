"""
YouTube Transcript Ingestion Plugin
==================================

Adaptation of the standalone YouTube ingestion script into the unified
ingestion plugin architecture used by the LAMB Knowledge Base Server.

Features:
 - Accepts a single YouTube URL (plugin param: video_url) or a text file whose
   first non-empty line(s) contain YouTube URLs (one per line)
 - Fetches transcript using youtube-transcript-api directly (no external CLI)
 - Chunks transcript pieces by target duration (default 60s)
 - Cleans text and preserves original raw text per piece
 - Returns standard chunk objects with rich metadata for downstream storage

Usage (API Example):
  plugin_name: youtube_transcript_ingest
  plugin_params: {
      "video_url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
      "language": "en",                 # optional (default: en)
      "chunk_duration": 60,               # seconds, optional
      "proxy_url": "http://proxy:8080"   # optional
  }

If you upload a small text file containing multiple video URLs (one per line)
you may omit video_url; all listed videos will be ingested sequentially and
their chunks aggregated. (Note: current implementation does sequential fetch.)

Environment Toggle:
  Set PLUGIN_YOUTUBE_TRANSCRIPT_INGEST=DISABLE to disable auto-registration.
"""

from __future__ import annotations

import re
import os
from typing import Dict, List, Any, Optional, Iterable
from datetime import datetime

try:
    from youtube_transcript_api import (
        NoTranscriptFound,
        TranscriptsDisabled,
        YouTubeTranscriptApi,
    )
    _YT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _YT_AVAILABLE = False

from .base import IngestPlugin, PluginRegistry


def _parse_youtube_url(url: str) -> Optional[str]:
    """Extract a YouTube video ID from a URL.

    Returns None if it cannot be parsed.
    """
    url = url.strip()
    # Already an 11-char id?
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    pattern_watch = re.compile(r"(?:v=)([A-Za-z0-9_-]{11})")
    pattern_short = re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})")
    pattern_embed = re.compile(r"embed/([A-Za-z0-9_-]{11})")

    for pattern in (pattern_watch, pattern_short, pattern_embed):
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


def _seconds_to_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def _clean_text(text: str) -> str:
    """Light normalization & artifact removal."""
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"\[.*?\]", "", text)  # [Music], [Applause]
    text = re.sub(r"\(.*?\)", "", text)  # (inaudible)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"([.!?])\s*([a-z])", r"\1 \2", text)
    return text.strip()


def _chunk_transcript(pieces: List[Dict[str, Any]], chunk_duration: float) -> List[Dict[str, Any]]:
    """Group transcript pieces into chunks not exceeding target duration."""
    chunks: List[Dict[str, Any]] = []
    current = {"start": 0.0, "end": 0.0, "text_parts": [], "original_text_parts": []}

    for p in pieces:
        raw_text = p.get("text", "")
        cleaned = _clean_text(raw_text)
        if not cleaned:
            continue
        if not current["text_parts"]:
            current["start"] = p["start"]
        current["text_parts"].append(cleaned)
        current["original_text_parts"].append(raw_text)
        current["end"] = p["start"] + p.get("duration", 0)

        if current["end"] - current["start"] >= chunk_duration:
            chunks.append(current)
            current = {"start": 0.0, "end": 0.0, "text_parts": [], "original_text_parts": []}

    if current["text_parts"]:
        chunks.append(current)
    return chunks


def _fetch_transcript(video_id: str, languages: Iterable[str], proxy_url: Optional[str]) -> List[Dict[str, Any]]:
    """Fetch raw transcript pieces using youtube-transcript-api."""
    if not _YT_AVAILABLE:
        raise ImportError(
            'youtube-transcript-api not installed. Install with "pip install youtube-transcript-api".'
        )

    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
    try:
        transcript = transcript_list.find_transcript(list(languages))
    except NoTranscriptFound:
        # Fallback to English only
        transcript = transcript_list.find_transcript(["en"])  # may raise again

    # Each element: {text, start, duration}
    return transcript.fetch()


@PluginRegistry.register
class YouTubeTranscriptIngestPlugin(IngestPlugin):
    """Ingest YouTube video transcript(s) as document chunks.

    Unlike file-based plugins, this can work with a remote resource. A placeholder
    file may still be supplied by the ingestion pipeline; its path is accepted but
    not required if `video_url` param is provided.
    """

    name = "youtube_transcript_ingest"
    kind = "remote-ingest"
    description = "Ingest YouTube video transcripts via API with time-based chunking"
    # We allow providing a text file containing URLs; advertise txt support.
    supported_file_types = {"txt"}

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:  # noqa: D401
        return {
            "video_url": {
                "type": "string",
                "description": "Full YouTube video URL. If omitted, the uploaded text file is read for URLs (one per line).",
                "required": False,
            },
            "language": {
                "type": "string",
                "description": "Preferred subtitle language code (ISO 639-1).",
                "default": "en",
                "required": False,
            },
            "chunk_duration": {
                "type": "number",
                "description": "Target chunk duration in seconds.",
                "default": 60,
                "required": False,
            },
            "proxy_url": {
                "type": "string",
                "description": "Optional proxy URL for transcript API calls.",
                "required": False,
            },
        }

    # Helper -----------------------------------------------------------------
    def _extract_urls_from_file(self, file_path: str) -> List[str]:
        urls: List[str] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and ("youtu.be/" in line or "youtube.com" in line):
                        urls.append(line)
        except Exception:
            # Ignore file read issues; treat as no URLs
            pass
        return urls

    def ingest(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:  # noqa: D401
        video_url: Optional[str] = kwargs.get("video_url")
        language: str = kwargs.get("language", "en")
        chunk_duration: float = float(kwargs.get("chunk_duration", 60))
        proxy_url: Optional[str] = kwargs.get("proxy_url")
        file_url: str = kwargs.get("file_url", "")  # supplied by ingestion service

        urls: List[str] = []
        if video_url:
            urls.append(video_url)
        else:
            urls.extend(self._extract_urls_from_file(file_path))

        if not urls:
            raise ValueError(
                "No video_url provided and no YouTube URLs found in file. Provide plugin param 'video_url' or upload a txt file containing URLs."
            )

        all_chunks: List[Dict[str, Any]] = []
        for url in urls:
            video_id = _parse_youtube_url(url)
            if not video_id:
                continue  # skip invalid
            try:
                pieces = _fetch_transcript(video_id, [language], proxy_url)
            except (NoTranscriptFound, TranscriptsDisabled) as e:  # pragma: no cover
                # Skip videos without transcripts
                continue
            except Exception as e:  # pragma: no cover
                raise ValueError(f"Failed to fetch transcript for {url}: {e}")

            chunk_objs = _chunk_transcript(pieces, chunk_duration)

            # Build documents list for this video
            total = len(chunk_objs)
            for idx, c in enumerate(chunk_objs):
                cleaned_text = " ".join(c["text_parts"]).strip()
                original_text = " ".join(c["original_text_parts"]).strip()
                start_ts = _seconds_to_timestamp(c["start"]) if c["start"] else "00:00:00,000"
                end_ts = _seconds_to_timestamp(c["end"]) if c["end"] else start_ts

                metadata = {
                    "ingestion_plugin": self.name,
                    "source_url": url,
                    "video_id": video_id,
                    "language": language,
                    "chunk_index": idx,
                    "chunk_count": total,
                    "start_time": c["start"],
                    "end_time": c["end"],
                    "start_timestamp": start_ts,
                    "end_timestamp": end_ts,
                    "chunk_duration_target": chunk_duration,
                    "original_text_sample": original_text[:200],
                    "file_url": file_url,
                    "retrieval_timestamp": datetime.utcnow().isoformat(),
                    "plugin_version": "1.0.0",
                }

                all_chunks.append({
                    "text": cleaned_text,
                    "metadata": metadata,
                })

        if not all_chunks:
            raise ValueError("No chunks produced from provided YouTube URL(s).")

        return all_chunks
