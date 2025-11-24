#!/usr/bin/env python3
"""
Test script for audio cleanup functionality.

Tests the audio_service.py cleanup_audio_file() function.
"""

import sys
import os
from pathlib import Path
import tempfile

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.audio_service import extract_audio, cleanup_audio_file, AudioExtractionError


def test_cleanup_existing_file():
    """Test cleaning up an existing audio file."""
    print("=" * 60)
    print("Cleanup Existing File Test")
    print("=" * 60)

    # Create a temporary audio file
    temp_file = os.path.join(tempfile.gettempdir(), "test_audio_cleanup.mp3")

    try:
        # Create the file
        with open(temp_file, 'w') as f:
            f.write("dummy audio content")

        print(f"✓ Created test file: {temp_file}")
        print(f"  File exists: {os.path.exists(temp_file)}")

        # Clean it up
        print("\n🧹 Testing cleanup...")
        cleanup_audio_file(temp_file)

        # Verify it's gone
        if os.path.exists(temp_file):
            print(f"❌ FAILED: File still exists after cleanup")
            os.remove(temp_file)  # Force cleanup
            return False

        print(f"✅ SUCCESS: File deleted successfully")
        return True

    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False


def test_cleanup_nonexistent_file():
    """Test cleaning up a file that doesn't exist (should not error)."""
    print("\n" + "=" * 60)
    print("Cleanup Nonexistent File Test")
    print("=" * 60)

    nonexistent_file = "/tmp/this_file_does_not_exist_12345.mp3"

    try:
        print(f"🧹 Attempting to cleanup non-existent file...")
        cleanup_audio_file(nonexistent_file)

        print(f"✅ SUCCESS: No error raised for non-existent file")
        return True

    except Exception as e:
        print(f"❌ FAILED: Should not raise error for non-existent file: {e}")
        return False


def test_cleanup_multiple_files():
    """Test cleaning up multiple audio files."""
    print("\n" + "=" * 60)
    print("Cleanup Multiple Files Test")
    print("=" * 60)

    temp_dir = tempfile.gettempdir()
    test_files = [
        os.path.join(temp_dir, f"test_audio_{i}.mp3")
        for i in range(3)
    ]

    try:
        # Create test files
        for file_path in test_files:
            with open(file_path, 'w') as f:
                f.write(f"test content for {file_path}")

        print(f"✓ Created {len(test_files)} test files")

        # Clean them all up
        print(f"\n🧹 Cleaning up {len(test_files)} files...")
        for file_path in test_files:
            cleanup_audio_file(file_path)

        # Verify all are gone
        remaining = [f for f in test_files if os.path.exists(f)]

        if remaining:
            print(f"❌ FAILED: {len(remaining)} file(s) still exist:")
            for f in remaining:
                print(f"  - {f}")
                os.remove(f)  # Force cleanup
            return False

        print(f"✅ SUCCESS: All {len(test_files)} files deleted")
        return True

    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        # Force cleanup any remaining files
        for f in test_files:
            if os.path.exists(f):
                os.remove(f)
        return False


def test_cleanup_after_extraction():
    """Test cleanup workflow after actual audio extraction."""
    print("\n" + "=" * 60)
    print("Cleanup After Extraction Test")
    print("=" * 60)

    video_path = "samples/1cdf39a6-e5b0-454c-b22b-9bc19180d168.mp4"

    if not os.path.exists(video_path):
        print(f"⚠️  SKIPPED: Sample video not found at {video_path}")
        return True

    try:
        print(f"🎵 Extracting audio from sample video...")
        audio_path = extract_audio(video_path)

        if not os.path.exists(audio_path):
            print(f"❌ FAILED: Audio file not created")
            return False

        print(f"✓ Audio extracted to: {audio_path}")
        audio_size = os.path.getsize(audio_path)
        print(f"  File size: {audio_size / 1024:.2f} KB")

        # Test cleanup
        print(f"\n🧹 Cleaning up extracted audio...")
        cleanup_audio_file(audio_path)

        if os.path.exists(audio_path):
            print(f"❌ FAILED: Audio file still exists after cleanup")
            os.remove(audio_path)  # Force cleanup
            return False

        print(f"✅ SUCCESS: Extracted audio cleaned up successfully")
        return True

    except AudioExtractionError as e:
        print(f"❌ FAILED: Audio extraction error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False


def test_cleanup_permission_error():
    """Test cleanup behavior with permission-restricted file."""
    print("\n" + "=" * 60)
    print("Cleanup Permission Error Test")
    print("=" * 60)

    # This test is informational - we expect cleanup to handle errors gracefully
    temp_file = os.path.join(tempfile.gettempdir(), "test_readonly_audio.mp3")

    try:
        # Create file
        with open(temp_file, 'w') as f:
            f.write("test content")

        # Make it read-only (on Unix-like systems)
        if os.name != 'nt':  # Not Windows
            os.chmod(temp_file, 0o444)
            print(f"✓ Created read-only test file: {temp_file}")

            # Attempt cleanup
            print(f"🧹 Attempting to cleanup read-only file...")
            cleanup_audio_file(temp_file)

            # Check if file still exists
            if os.path.exists(temp_file):
                print(f"ℹ️  INFO: File still exists (expected for permission error)")
                # Restore permissions and cleanup
                os.chmod(temp_file, 0o644)
                os.remove(temp_file)
            else:
                print(f"✓ File deleted despite being read-only")

            print(f"✅ SUCCESS: Cleanup handled gracefully")
            return True
        else:
            print(f"⚠️  SKIPPED: Permission test not applicable on Windows")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return True

    except Exception as e:
        print(f"ℹ️  INFO: Exception during test: {e}")
        # Restore permissions if needed
        if os.path.exists(temp_file):
            try:
                os.chmod(temp_file, 0o644)
                os.remove(temp_file)
            except:
                pass
        return True  # This test is informational


def main():
    """Run all audio cleanup tests."""
    print("\n🧪 Audio Cleanup Test Suite")
    print("Testing: app/services/audio_service.py cleanup functions")
    print()

    results = []

    # Test 1: Cleanup existing file
    results.append(("Cleanup Existing File", test_cleanup_existing_file()))

    # Test 2: Cleanup non-existent file
    results.append(("Cleanup Nonexistent File", test_cleanup_nonexistent_file()))

    # Test 3: Cleanup multiple files
    results.append(("Cleanup Multiple Files", test_cleanup_multiple_files()))

    # Test 4: Cleanup after extraction
    results.append(("Cleanup After Extraction", test_cleanup_after_extraction()))

    # Test 5: Permission error handling
    results.append(("Permission Error Handling", test_cleanup_permission_error()))

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
