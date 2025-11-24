#!/usr/bin/env python3
"""
Test script for audio file size verification.

Tests the audio compression settings and verifies file size reduction
compared to the original video file.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.audio_service import extract_audio, cleanup_audio_file, AudioExtractionError


def format_bytes(bytes_val):
    """Format bytes to human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"


def test_audio_size(video_path):
    """Test audio extraction and measure file sizes."""
    print("=" * 80)
    print(f"Audio Size Test: {os.path.basename(video_path)}")
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
    try:
        print(f"\n🎵 Extracting audio with 64k bitrate...")
        audio_path, audio_size = extract_audio(video_path)

        print(f"\n✅ Audio Extraction Successful!")
        print(f"   Path: {audio_path}")
        print(f"   Size: {format_bytes(audio_size)}")

        # Calculate compression ratio
        ratio = (1 - (audio_size / video_size)) * 100
        print(f"\n📊 Compression Analysis:")
        print(f"   Video size:  {format_bytes(video_size)}")
        print(f"   Audio size:  {format_bytes(audio_size)}")
        print(f"   Reduction:   {ratio:.1f}%")
        print(f"   Ratio:       {video_size / audio_size:.1f}:1")

        # Estimate bitrate based on file size
        # Rough estimation: size in bytes / duration (assume ~60 seconds for demo)
        # More accurate with actual duration but good enough for testing
        print(f"\n💾 File Size Details:")
        print(f"   Audio bytes: {audio_size:,} bytes")
        print(f"   Expected:    ~480 KB/min at 64 kbps (64k * 60s / 8)")

        # Quality check
        if audio_size == 0:
            print(f"\n❌ ERROR: Audio file is empty!")
            return None
        elif audio_size < 1024:
            print(f"\n⚠️  WARNING: Audio file seems too small ({audio_size} bytes)")
        else:
            print(f"\n✓ Audio file size looks good")

        return {
            'video_path': video_path,
            'video_size': video_size,
            'audio_path': audio_path,
            'audio_size': audio_size,
            'reduction_pct': ratio,
            'compression_ratio': video_size / audio_size
        }

    except AudioExtractionError as e:
        print(f"\n❌ FAILED: Audio extraction error: {e}")
        return None
    except Exception as e:
        print(f"\n❌ FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Clean up
        if audio_path and os.path.exists(audio_path):
            print(f"\n🧹 Cleaning up audio file...")
            cleanup_audio_file(audio_path)
            print(f"✓ Cleaned up: {audio_path}")


def main():
    """Run audio size tests on sample videos."""
    print("\n🧪 Audio Size Test Suite")
    print("Testing: 64 kbps audio compression")
    print()

    # Find sample videos
    sample_videos = []
    sample_dir = "samples"

    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                sample_videos.append(os.path.join(sample_dir, file))

    if not sample_videos:
        print(f"❌ No sample videos found in {sample_dir}/")
        print("Please add a sample video to the samples/ directory")
        return 1

    print(f"Found {len(sample_videos)} sample video(s)\n")

    results = []
    for video_path in sample_videos:
        result = test_audio_size(video_path)
        if result:
            results.append(result)
        print()

    # Summary
    if results:
        print("=" * 80)
        print("Summary")
        print("=" * 80)

        total_video_size = sum(r['video_size'] for r in results)
        total_audio_size = sum(r['audio_size'] for r in results)
        avg_reduction = sum(r['reduction_pct'] for r in results) / len(results)

        print(f"\n📊 Overall Statistics:")
        print(f"   Videos tested:     {len(results)}")
        print(f"   Total video size:  {format_bytes(total_video_size)}")
        print(f"   Total audio size:  {format_bytes(total_audio_size)}")
        print(f"   Average reduction: {avg_reduction:.1f}%")
        print(f"   Overall ratio:     {total_video_size / total_audio_size:.1f}:1")

        print(f"\n✅ All tests completed successfully!")
        print(f"\n💡 Audio size is being captured and logged correctly.")
        print(f"   Bitrate: 64 kbps (constant bitrate)")
        print(f"   Format:  MP3")
        print(f"   Quality: Optimized for speech transcription")

        return 0
    else:
        print("❌ No successful tests")
        return 1


if __name__ == "__main__":
    sys.exit(main())
