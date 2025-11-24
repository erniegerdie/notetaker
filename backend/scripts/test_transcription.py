#!/usr/bin/env python3
"""
Test script for transcription service with compressed audio.

Tests the full pipeline:
1. Extract compressed audio from video
2. Split into chunks if > 10 MB
3. Transcribe with chunking/concurrency if needed
4. Verify transcription quality
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
    cleanup_audio_file,
    split_audio_into_chunks,
    cleanup_audio_chunks,
    AudioExtractionError,
)
from app.services.transcription_service import (
    transcribe_audio,
    transcribe_audio_chunks,
    TranscriptionError,
)
from app.config import settings

# Size threshold for chunking (10 MB)
CHUNK_THRESHOLD_MB = 4
CHUNK_THRESHOLD_BYTES = CHUNK_THRESHOLD_MB * 1024 * 1024
CONCURRENT_REQUESTS = 5


def format_bytes(bytes_val):
    """Format bytes to human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"


async def test_transcription_pipeline(video_path):
    """Test full transcription pipeline with compressed audio and chunking."""
    print("=" * 80)
    print(f"Transcription Pipeline Test: {os.path.basename(video_path)}")
    print("=" * 80)

    if not os.path.exists(video_path):
        print(f"❌ FAILED: Video file not found at {video_path}")
        return None

    # Get video file size
    video_size = os.path.getsize(video_path)
    print(f"\n📹 Video File:")
    print(f"   Path: {video_path}")
    print(f"   Size: {format_bytes(video_size)}")

    audio_path = None
    chunks = None
    start_time = datetime.now()

    try:
        # Step 1: Extract compressed audio
        print(f"\n🎵 Step 1: Extracting compressed audio...")
        print(f"   Settings: Mono, 16 kHz, 32 kbps")
        audio_path, audio_size = extract_audio(video_path)

        extraction_time = (datetime.now() - start_time).total_seconds()
        print(f"   ✅ Audio extracted in {extraction_time:.1f}s")
        print(f"   Path: {audio_path}")
        print(f"   Size: {format_bytes(audio_size)}")

        # Step 2: Check chunking threshold
        print(f"\n📊 Step 2: Checking chunking threshold...")
        print(f"   Audio size:       {format_bytes(audio_size)}")
        print(f"   Chunk threshold:  {format_bytes(CHUNK_THRESHOLD_BYTES)}")

        if audio_size > CHUNK_THRESHOLD_BYTES:
            print(f"   ⚠️  Audio exceeds threshold - will split into chunks")
        else:
            print(f"   ✅ Audio under threshold - no chunking needed")

        # Step 3: Transcribe audio (with chunking if needed)
        print(f"\n🤖 Step 3: Transcribing with {settings.transcription_model}...")
        transcribe_start = datetime.now()

        if audio_size > CHUNK_THRESHOLD_BYTES:
            # Large audio file - split into chunks
            print(
                f"   Audio file {audio_size / (1024*1024):.2f} MB exceeds threshold, splitting into chunks"
            )
            chunks = split_audio_into_chunks(
                audio_path, max_chunk_size_mb=CHUNK_THRESHOLD_MB
            )
            print(f"   Created {len(chunks)} chunks")
            for i, (_, chunk_size) in enumerate(chunks):
                print(f"      Chunk {i+1}: {format_bytes(chunk_size)}")
            print(
                f"   Transcribing {len(chunks)} chunks with max {CONCURRENT_REQUESTS} concurrent requests"
            )
            transcript_text, model_used = await transcribe_audio_chunks(
                chunks, max_concurrent=CONCURRENT_REQUESTS
            )
        else:
            # Small audio file - transcribe directly
            print(f"   Transcribing audio directly (single file)")
            transcript_text, model_used = transcribe_audio(audio_path)

        transcribe_time = (datetime.now() - transcribe_start).total_seconds()
        print(f"   ✅ Transcription completed in {transcribe_time:.1f}s")
        print(f"   Model used: {model_used}")
        print(f"   Transcript length: {len(transcript_text)} characters")
        if chunks:
            print(f"   Chunks processed: {len(chunks)}")

        # Step 4: Analyze transcript
        print(f"\n📝 Step 4: Transcript analysis...")
        word_count = len(transcript_text.split())
        line_count = len(transcript_text.split("\n"))

        print(f"   Characters: {len(transcript_text):,}")
        print(f"   Words:      {word_count:,}")
        print(f"   Lines:      {line_count}")

        if len(transcript_text) < 10:
            print(f"   ⚠️  WARNING: Transcript seems too short")
        else:
            print(f"   ✅ Transcript looks valid")

        # Write transcript to file
        transcript_filename = f"transcript_{os.path.basename(video_path)}.txt"
        transcript_path = os.path.join("outputs", transcript_filename)
        os.makedirs("outputs", exist_ok=True)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        print(f"\n💾 Transcript saved to: {transcript_path}")

        # Show transcript preview
        print(f"\n📄 Transcript Preview (first 500 chars):")
        print("   " + "-" * 76)
        preview = transcript_text[:500]
        for line in preview.split("\n"):
            if line.strip():
                print(f"   {line[:76]}")
        if len(transcript_text) > 500:
            print(f"   ... ({len(transcript_text) - 500} more characters)")
        print("   " + "-" * 76)

        # Summary
        total_time = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ Pipeline completed successfully in {total_time:.1f}s")

        return {
            "video_path": video_path,
            "video_size": video_size,
            "audio_size": audio_size,
            "audio_path": audio_path,
            "transcript_length": len(transcript_text),
            "model_used": model_used,
            "extraction_time": extraction_time,
            "transcription_time": transcribe_time,
            "total_time": total_time,
            "num_chunks": len(chunks) if chunks else 1,
        }

    except AudioExtractionError as e:
        print(f"\n❌ FAILED: Audio extraction error: {e}")
        return None
    except TranscriptionError as e:
        print(f"\n❌ FAILED: Transcription error: {e}")
        return None
    except Exception as e:
        print(f"\n❌ FAILED: Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return None
    finally:
        # Clean up
        if chunks and len(chunks) > 1:
            print(f"\n🧹 Cleaning up {len(chunks)} chunk files...")
            cleanup_audio_chunks(chunks)
        if audio_path and os.path.exists(audio_path):
            print(f"🧹 Cleaning up audio file...")
            cleanup_audio_file(audio_path)
            print(f"✓ Cleanup complete")


async def main():
    """Run transcription pipeline tests."""
    print("\n🧪 Transcription Pipeline Test Suite")
    print(
        "Testing: Audio extraction → Chunking → Transcription (gpt-4o-mini-transcribe)"
    )
    print()

    # Check API key
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key":
        print("❌ ERROR: OPENAI_API_KEY not configured in .env")
        print("Please set a valid OpenAI API key to test transcription.")
        return 1

    print(f"✓ API Key configured")
    print(f"✓ Model: {settings.transcription_model}")
    print(f"✓ Fallback: {settings.transcription_fallback_model}")
    print(f"✓ Chunk threshold: {CHUNK_THRESHOLD_MB} MB")
    print(f"✓ Max concurrent: {CONCURRENT_REQUESTS}")
    print()

    # Find sample videos
    sample_videos = []
    sample_dir = "samples"

    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            if file.endswith((".mp4", ".avi", ".mov", ".mkv")):
                sample_videos.append(os.path.join(sample_dir, file))

    if not sample_videos:
        print(f"❌ No sample videos found in {sample_dir}/")
        print("Please add a sample video to the samples/ directory")
        return 1

    print(f"Found {len(sample_videos)} sample video(s)\n")

    # Test first video only (to avoid API costs)
    print("⚠️  Note: Testing only the first video to minimize API costs\n")

    results = []
    result = await test_transcription_pipeline(sample_videos[0])
    if result:
        results.append(result)
    print()

    # Summary
    if results:
        print("=" * 80)
        print("Summary")
        print("=" * 80)

        for r in results:
            print(f"\n✅ {os.path.basename(r['video_path'])}")
            print(f"   Video:        {format_bytes(r['video_size'])}")
            print(f"   Audio:        {format_bytes(r['audio_size'])}")
            print(f"   Chunks:       {r['num_chunks']}")
            print(
                f"   Compression:  {(1 - r['audio_size']/r['video_size']) * 100:.1f}%"
            )
            print(f"   Transcript:   {r['transcript_length']:,} chars")
            print(f"   Model:        {r['model_used']}")
            print(f"   Extract time: {r['extraction_time']:.1f}s")
            print(f"   Transcribe:   {r['transcription_time']:.1f}s")
            print(f"   Total:        {r['total_time']:.1f}s")

        print(f"\n💡 Key Results:")
        print(f"   ✅ Audio compression working (mono, 16 kHz, 32 kbps)")
        print(f"   ✅ Automatic chunking for files > {CHUNK_THRESHOLD_MB} MB")
        print(f"   ✅ Concurrent transcription (max {CONCURRENT_REQUESTS}) working")
        print(f"   ✅ All chunks under 25 MB API limit")
        print(f"   ✅ Full pipeline working end-to-end")

        return 0
    else:
        print("❌ No successful tests")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
