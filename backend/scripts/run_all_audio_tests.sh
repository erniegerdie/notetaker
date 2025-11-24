#!/bin/bash

# Run all audio service test scripts
# Usage: ./run_all_audio_tests.sh

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Audio Service Test Suite Runner                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Check if sample video exists
if [ ! -f "samples/1cdf39a6-e5b0-454c-b22b-9bc19180d168.mp4" ]; then
    echo "⚠️  Warning: Sample video not found at samples/1cdf39a6-e5b0-454c-b22b-9bc19180d168.mp4"
    echo "   Some tests may be skipped."
    echo ""
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ Error: ffmpeg is not installed"
    echo ""
    echo "Please install ffmpeg:"
    echo "  macOS:        brew install ffmpeg"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  Windows:      Download from https://ffmpeg.org/"
    exit 1
fi

echo "✓ ffmpeg found: $(ffmpeg -version | head -n1)"
echo ""

# Array to store test results
declare -a test_results
declare -a test_names

# Run test 1: Audio extraction
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Audio Extraction"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run python scripts/test_audio_extraction.py; then
    test_results+=("PASS")
    test_names+=("Audio Extraction")
else
    test_results+=("FAIL")
    test_names+=("Audio Extraction")
fi
echo ""

# Run test 2: Audio cleanup
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Audio Cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run python scripts/test_audio_cleanup.py; then
    test_results+=("PASS")
    test_names+=("Audio Cleanup")
else
    test_results+=("FAIL")
    test_names+=("Audio Cleanup")
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

passed=0
failed=0

for i in "${!test_results[@]}"; do
    if [ "${test_results[$i]}" == "PASS" ]; then
        echo "✅ PASSED: ${test_names[$i]}"
        ((passed++))
    else
        echo "❌ FAILED: ${test_names[$i]}"
        ((failed++))
    fi
done

total=${#test_results[@]}
echo ""
echo "Results: $passed/$total test suites passed"

if [ $failed -eq 0 ]; then
    echo ""
    echo "🎉 All test suites passed!"
    exit 0
else
    echo ""
    echo "⚠️  $failed test suite(s) failed"
    exit 1
fi
