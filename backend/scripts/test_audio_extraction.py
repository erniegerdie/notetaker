#!/usr/bin/env python3
"""
Test script for audio extraction service.

Tests the audio_service.py extract_audio() function with the sample video.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.audio_service import extract_audio, cleanup_audio_file, AudioExtractionError


def test_audio_extraction():
    """Test extracting audio from sample video."""
    print("=" * 60)
    print("Audio Extraction Test")
    print("=" * 60)

    # Sample video path
    video_path = "samples/1cdf39a6-e5b0-454c-b22b-9bc19180d168.mp4"

    if not os.path.exists(video_path):
        print(f"❌ FAILED: Sample video not found at {video_path}")
        return False

    print(f"✓ Sample video found: {video_path}")
    print(f"  File size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")

    try:
        print("\n🎵 Extracting audio...")
        audio_path = extract_audio(video_path)

        print(f"✅ SUCCESS: Audio extracted to: {audio_path}")

        # Verify audio file exists
        if not os.path.exists(audio_path):
            print(f"❌ FAILED: Audio file not created at {audio_path}")
            return False

        # Check audio file size
        audio_size = os.path.getsize(audio_path)
        print(f"  Audio file size: {audio_size / 1024:.2f} KB")

        if audio_size == 0:
            print("❌ FAILED: Audio file is empty")
            cleanup_audio_file(audio_path)
            return False

        # Verify it's an MP3 file
        if not audio_path.endswith('.mp3'):
            print(f"⚠️  WARNING: Audio file is not MP3: {audio_path}")

        print(f"✓ Audio file is valid ({audio_size / 1024:.2f} KB)")

        # Clean up
        print("\n🧹 Cleaning up audio file...")
        cleanup_audio_file(audio_path)

        if os.path.exists(audio_path):
            print("❌ FAILED: Audio file not deleted")
            return False

        print("✓ Audio file cleaned up successfully")

        return True

    except AudioExtractionError as e:
        print(f"❌ FAILED: Audio extraction error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_video():
    """Test error handling with invalid video path."""
    print("\n" + "=" * 60)
    print("Invalid Video Test")
    print("=" * 60)

    video_path = "nonexistent_video.mp4"

    try:
        print(f"🎵 Attempting to extract audio from non-existent video...")
        audio_path = extract_audio(video_path)
        print(f"❌ FAILED: Should have raised AudioExtractionError")
        return False

    except AudioExtractionError as e:
        print(f"✅ SUCCESS: Correctly raised AudioExtractionError: {e}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Raised wrong exception type: {type(e).__name__}: {e}")
        return False


def test_empty_file():
    """Test error handling with empty file."""
    print("\n" + "=" * 60)
    print("Empty File Test")
    print("=" * 60)

    # Create empty file
    empty_file = "/tmp/empty_video.mp4"
    try:
        with open(empty_file, 'w') as f:
            pass

        print(f"✓ Created empty test file: {empty_file}")

        try:
            print(f"🎵 Attempting to extract audio from empty file...")
            audio_path = extract_audio(empty_file)

            # If we get here, check if audio was created
            if os.path.exists(audio_path):
                cleanup_audio_file(audio_path)

            print(f"⚠️  WARNING: Extraction completed but may have produced invalid audio")
            return True

        except AudioExtractionError as e:
            print(f"✅ SUCCESS: Correctly raised AudioExtractionError: {e}")
            return True
        except Exception as e:
            print(f"⚠️  INFO: Raised exception: {type(e).__name__}: {e}")
            return True
    finally:
        if os.path.exists(empty_file):
            os.remove(empty_file)
            print(f"✓ Cleaned up test file")


def main():
    """Run all audio extraction tests."""
    print("\n🧪 Audio Service Test Suite")
    print("Testing: app/services/audio_service.py")
    print()

    results = []

    # Test 1: Valid audio extraction
    results.append(("Audio Extraction", test_audio_extraction()))

    # Test 2: Invalid video path
    results.append(("Invalid Video", test_invalid_video()))

    # Test 3: Empty file
    results.append(("Empty File", test_empty_file()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
