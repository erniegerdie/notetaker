# Test Scripts

Manual test scripts for backend services (no pytest required).

## Overview

These scripts test individual service functions directly without requiring a running API server or test framework.

## Test Scripts

### Audio Service Tests

Tests for `app/services/audio_service.py`:

1. **test_audio_extraction.py** - Tests audio extraction from video files
   - Valid video extraction
   - Invalid video path handling
   - Empty file handling

2. **test_audio_cleanup.py** - Tests audio file cleanup
   - Cleanup existing files
   - Cleanup non-existent files (graceful handling)
   - Cleanup multiple files
   - Cleanup after extraction
   - Permission error handling

### Test Runner

**run_all_audio_tests.sh** - Runs all audio service tests and provides summary

## Prerequisites

1. **ffmpeg** - Required for audio extraction
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

2. **Sample video** - Located at `samples/1cdf39a6-e5b0-454c-b22b-9bc19180d168.mp4`

3. **Python dependencies** - Installed via uv
   ```bash
   uv sync
   ```

## Running Tests

### Run All Tests

```bash
cd backend
./scripts/run_all_audio_tests.sh
```

### Run Individual Tests

```bash
# Audio extraction tests
uv run python scripts/test_audio_extraction.py

# Audio cleanup tests
uv run python scripts/test_audio_cleanup.py
```

### Run from Backend Directory

```bash
cd backend

# All tests
./scripts/run_all_audio_tests.sh

# Individual test
uv run python scripts/test_audio_extraction.py
```

## Test Output

Tests provide colored output with clear pass/fail indicators:

```
✅ SUCCESS: Test passed
❌ FAILED: Test failed
⚠️  WARNING: Non-critical issue
ℹ️  INFO: Informational message
```

## Sample Test Run

```bash
$ ./scripts/run_all_audio_tests.sh

╔════════════════════════════════════════════════════════════╗
║       Audio Service Test Suite Runner                     ║
╚════════════════════════════════════════════════════════════╝

✓ ffmpeg found: ffmpeg version 6.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test 1: Audio Extraction
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 Audio Service Test Suite
Testing: app/services/audio_service.py

============================================================
Audio Extraction Test
============================================================
✓ Sample video found: samples/1cdf39a6-e5b0-454c-b22b-9bc19180d168.mp4
  File size: 7.50 MB

🎵 Extracting audio...
✅ SUCCESS: Audio extracted to: /tmp/1cdf39a6-e5b0-454c-b22b-9bc19180d168_audio.mp3
  Audio file size: 356.24 KB
✓ Audio file is valid (356.24 KB)

🧹 Cleaning up audio file...
✓ Audio file cleaned up successfully

...

╔════════════════════════════════════════════════════════════╗
║                    Test Summary                            ║
╚════════════════════════════════════════════════════════════╝

✅ PASSED: Audio Extraction
✅ PASSED: Audio Cleanup

Results: 2/2 test suites passed

🎉 All test suites passed!
```

## Test Details

### Audio Extraction Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| Valid extraction | Extract from sample MP4 | Audio MP3 created |
| Invalid path | Non-existent video | AudioExtractionError raised |
| Empty file | Empty video file | Error or warning |

### Audio Cleanup Tests

| Test | Description | Expected Result |
|------|-------------|-----------------|
| Existing file | Delete valid audio file | File removed |
| Non-existent | Delete missing file | No error |
| Multiple files | Delete 3+ files | All removed |
| After extraction | Cleanup extracted audio | File removed |
| Permission error | Readonly file cleanup | Graceful handling |

## Adding New Tests

To add tests for other services:

1. Create test script in `scripts/`:
   ```python
   #!/usr/bin/env python3
   import sys
   from pathlib import Path

   sys.path.insert(0, str(Path(__file__).parent.parent))

   from app.services.your_service import your_function

   def test_something():
       # Your test code
       pass

   if __name__ == "__main__":
       sys.exit(main())
   ```

2. Make it executable:
   ```bash
   chmod +x scripts/test_your_service.py
   ```

3. Update `run_all_tests.sh` to include new test

## Troubleshooting

### ffmpeg not found

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### Sample video not found

Ensure `samples/1cdf39a6-e5b0-454c-b22b-9bc19180d168.mp4` exists in backend directory.

### Module import errors

```bash
# Make sure you're in backend directory
cd backend

# Run with uv
uv run python scripts/test_audio_extraction.py
```

### Permission errors on cleanup tests

Some cleanup tests are informational - permission errors are handled gracefully and won't fail the test suite.

## CI/CD Integration

To run in CI/CD pipelines:

```bash
# Install ffmpeg in CI environment
apt-get update && apt-get install -y ffmpeg

# Run tests
cd backend
uv sync
./scripts/run_all_audio_tests.sh
```

## Notes

- Tests use the actual `app/services/audio_service.py` code
- No mocking - tests real ffmpeg integration
- Tests clean up after themselves (temp files removed)
- Safe to run repeatedly
- No external API calls required
