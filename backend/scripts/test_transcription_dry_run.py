#!/usr/bin/env python3
"""
Dry run test for transcription service setup.

Tests everything except the actual API call:
1. Extract compressed audio from video
2. Verify audio is under 25 MB limit
3. Verify API configuration
4. Show what would be sent to transcription service
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.audio_service import extract_audio, cleanup_audio_file, AudioExtractionError
from app.config import settings


def format_bytes(bytes_val):
    """Format bytes to human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"


def test_setup_dry_run(video_path):
    """Test setup without calling API."""
    print("=" * 80)
    print(f"Dry Run Test: {os.path.basename(video_path)}")
    print("=" * 80)

    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False

    video_size = os.path.getsize(video_path)
    print(f"\n📹 Video File:")
    print(f"   Size: {format_bytes(video_size)}")

    audio_path = None
    try:
        # Extract audio
        print(f"\n🎵 Extracting compressed audio...")
        print(f"   Format: Mono, 16 kHz, 32 kbps MP3")
        audio_path, audio_size = extract_audio(video_path)

        print(f"\n✅ Audio extracted:")
        print(f"   Size: {format_bytes(audio_size)}")
        print(f"   Path: {audio_path}")

        # Check size limit
        max_size = 25 * 1024 * 1024  # 25 MB
        size_pct = (audio_size / max_size) * 100

        print(f"\n📊 API Limit Check:")
        print(f"   Audio size: {format_bytes(audio_size)}")
        print(f"   API limit:  {format_bytes(max_size)}")
        print(f"   Usage:      {size_pct:.1f}%")

        if audio_size > max_size:
            print(f"   ❌ FAIL: Exceeds API limit!")
            return False
        else:
            print(f"   ✅ PASS: Under API limit")

        # Check API configuration
        print(f"\n🔑 API Configuration:")
        if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key":
            key_preview = settings.openai_api_key[:8] + "..." + settings.openai_api_key[-4:]
            print(f"   API Key: {key_preview} ✓")
        else:
            print(f"   API Key: Not configured ❌")
            return False

        print(f"   Model: {settings.transcription_model} ✓")
        print(f"   Fallback: {settings.transcription_fallback_model} ✓")

        # Summary
        print(f"\n✅ Setup Valid - Ready for Transcription")
        print(f"\n📋 Would send to API:")
        print(f"   File: {os.path.basename(audio_path)}")
        print(f"   Size: {format_bytes(audio_size)}")
        print(f"   Model: {settings.transcription_model}")

        return True

    except AudioExtractionError as e:
        print(f"\n❌ Audio extraction failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if audio_path and os.path.exists(audio_path):
            cleanup_audio_file(audio_path)


def main():
    """Run dry run tests."""
    print("\n🧪 Transcription Setup Dry Run")
    print("Testing: Configuration & Audio Compression (no API calls)")
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

    print(f"Found {len(sample_videos)} sample video(s)\n")

    results = []
    for video_path in sample_videos[:2]:  # Test first 2 videos
        result = test_setup_dry_run(video_path)
        results.append(result)
        print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    print(f"\n✅ Passed: {passed}/{total}")

    if passed == total:
        print(f"\n🎉 All setup checks passed!")
        print(f"\n💡 Ready to transcribe:")
        print(f"   • Audio compression working (under 25 MB)")
        print(f"   • API credentials configured")
        print(f"   • Model: {settings.transcription_model}")
        print(f"\n📝 To test actual transcription:")
        print(f"   cd backend && uv run python scripts/test_transcription.py")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
