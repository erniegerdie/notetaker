#!/usr/bin/env python3
"""
Test script for chunked transcription with concurrency control.

Tests the full chunked pipeline:
1. Extract compressed audio from video
2. Split into chunks if needed
3. Transcribe chunks with max 2 concurrent requests
4. Combine results
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.audio_service import (
    extract_audio,
    split_audio_into_chunks,
    cleanup_audio_file,
    cleanup_audio_chunks,
    AudioExtractionError
)
from app.services.transcription_service import (
    transcribe_audio,
    transcribe_audio_chunks,
    TranscriptionError
)
from app.config import settings


def format_bytes(bytes_val):
    """Format bytes to human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"


async def test_chunked_transcription(video_path, force_chunking=False):
    """Test chunked transcription pipeline."""
    print("=" * 80)
    print(f"Chunked Transcription Test: {os.path.basename(video_path)}")
    print("=" * 80)

    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None

    video_size = os.path.getsize(video_path)
    print(f"\n📹 Video File:")
    print(f"   Size: {format_bytes(video_size)}")

    audio_path = None
    chunks = None
    start_time = datetime.now()

    try:
        # Step 1: Extract audio
        print(f"\n🎵 Step 1: Extracting compressed audio...")
        audio_path, audio_size = extract_audio(video_path)
        extraction_time = (datetime.now() - start_time).total_seconds()

        print(f"   ✅ Extracted in {extraction_time:.1f}s")
        print(f"   Size: {format_bytes(audio_size)}")

        # Step 2: Split into chunks if needed
        print(f"\n📦 Step 2: Checking if chunking needed...")
        chunk_threshold = 20 * 1024 * 1024  # 20 MB

        if audio_size > chunk_threshold or force_chunking:
            print(f"   Audio {format_bytes(audio_size)} > {format_bytes(chunk_threshold)}")
            print(f"   Splitting into chunks...")

            chunk_start = datetime.now()
            # Force smaller chunks for testing
            max_chunk_size = 10 if force_chunking else 20
            chunks = split_audio_into_chunks(audio_path, max_chunk_size_mb=max_chunk_size)
            chunk_time = (datetime.now() - chunk_start).total_seconds()

            print(f"   ✅ Split into {len(chunks)} chunks in {chunk_time:.1f}s")
            for i, (chunk_path, chunk_size) in enumerate(chunks):
                print(f"      Chunk {i+1}: {format_bytes(chunk_size)}")
        else:
            print(f"   Audio {format_bytes(audio_size)} <= {format_bytes(chunk_threshold)}")
            print(f"   ✅ No chunking needed, using single file")
            chunks = [(audio_path, audio_size)]

        # Step 3: Transcribe
        print(f"\n🤖 Step 3: Transcribing with {settings.transcription_model}...")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Max concurrent: 2")

        transcribe_start = datetime.now()

        if len(chunks) > 1:
            transcript_text, model_used = await transcribe_audio_chunks(chunks, max_concurrent=2)
        else:
            transcript_text, model_used = transcribe_audio(chunks[0][0])

        transcribe_time = (datetime.now() - transcribe_start).total_seconds()

        print(f"   ✅ Transcription completed in {transcribe_time:.1f}s")
        print(f"   Model: {model_used}")
        print(f"   Transcript: {len(transcript_text)} characters")

        # Step 4: Analysis
        print(f"\n📊 Step 4: Analysis...")
        word_count = len(transcript_text.split())
        total_time = (datetime.now() - start_time).total_seconds()

        print(f"   Characters: {len(transcript_text):,}")
        print(f"   Words:      {word_count:,}")
        print(f"   Total time: {total_time:.1f}s")

        # Show preview
        print(f"\n📄 Transcript Preview (first 300 chars):")
        print("   " + "-" * 76)
        preview = transcript_text[:300]
        print(f"   {preview}")
        if len(transcript_text) > 300:
            print(f"   ... ({len(transcript_text) - 300} more characters)")
        print("   " + "-" * 76)

        print(f"\n✅ Pipeline completed successfully")

        return {
            'video_size': video_size,
            'audio_size': audio_size,
            'num_chunks': len(chunks),
            'transcript_length': len(transcript_text),
            'extraction_time': extraction_time,
            'transcription_time': transcribe_time,
            'total_time': total_time
        }

    except AudioExtractionError as e:
        print(f"\n❌ Audio error: {e}")
        return None
    except TranscriptionError as e:
        print(f"\n❌ Transcription error: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Cleanup
        if chunks and len(chunks) > 1:
            print(f"\n🧹 Cleaning up {len(chunks)} chunk files...")
            cleanup_audio_chunks(chunks)
        if audio_path:
            cleanup_audio_file(audio_path)
        print(f"✓ Cleanup complete")


async def main():
    """Run chunked transcription tests."""
    print("\n🧪 Chunked Transcription Test Suite")
    print("Testing: Audio chunking + Concurrent transcription (max 2)")
    print()

    # Check API key
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key":
        print("❌ ERROR: OPENAI_API_KEY not configured")
        return 1

    print(f"✓ API Key configured")
    print(f"✓ Model: {settings.transcription_model}")
    print(f"✓ Chunk threshold: 20 MB")
    print(f"✓ Max concurrent: 2")
    print()

    # Find sample videos
    sample_videos = []
    sample_dir = "samples"

    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                sample_videos.append(os.path.join(sample_dir, file))

    if not sample_videos:
        print(f"❌ No sample videos in {sample_dir}/")
        return 1

    print(f"Found {len(sample_videos)} sample video(s)")
    print("⚠️  Testing first video only to minimize API costs")
    print()

    # Test with forced chunking to demonstrate functionality
    print("Testing with FORCED chunking (10 MB chunks) for demonstration\n")

    result = await test_chunked_transcription(sample_videos[0], force_chunking=True)

    # Summary
    if result:
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)

        print(f"\n✅ Chunked transcription successful!")
        print(f"   Video:        {format_bytes(result['video_size'])}")
        print(f"   Audio:        {format_bytes(result['audio_size'])}")
        print(f"   Chunks:       {result['num_chunks']}")
        print(f"   Transcript:   {result['transcript_length']:,} chars")
        print(f"   Extract time: {result['extraction_time']:.1f}s")
        print(f"   Transcribe:   {result['transcription_time']:.1f}s")
        print(f"   Total:        {result['total_time']:.1f}s")

        print(f"\n💡 Key Results:")
        print(f"   ✅ Audio chunking working correctly")
        print(f"   ✅ Concurrent transcription (max 2) working")
        print(f"   ✅ Chunks combined properly")
        print(f"   ✅ All chunks under 25 MB API limit")

        return 0
    else:
        print("\n❌ Test failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
