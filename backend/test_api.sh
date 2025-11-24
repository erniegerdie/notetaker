#!/bin/bash

# Simple API test script for Video Transcription API

BASE_URL="http://localhost:8000"

echo "Testing Video Transcription API..."
echo

# Test 1: Health check
echo "1. Health check..."
curl -s "${BASE_URL}/health" | jq .
echo

# Test 2: Root endpoint
echo "2. Root endpoint..."
curl -s "${BASE_URL}/" | jq .
echo

# Test 3: List videos (should be empty initially)
echo "3. List videos..."
curl -s "${BASE_URL}/api/videos" | jq .
echo

# Test 4: Upload video (requires a video file)
if [ -f "$1" ]; then
    echo "4. Upload video: $1"
    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/videos/upload" -F "file=@$1")
    echo "$RESPONSE" | jq .

    VIDEO_ID=$(echo "$RESPONSE" | jq -r .id)

    if [ "$VIDEO_ID" != "null" ]; then
        echo
        echo "5. Check video status..."
        sleep 2
        curl -s "${BASE_URL}/api/videos/${VIDEO_ID}/status" | jq .

        echo
        echo "6. Waiting for processing (polling every 5 seconds)..."
        while true; do
            STATUS=$(curl -s "${BASE_URL}/api/videos/${VIDEO_ID}/status" | jq -r .status)
            echo "Status: $STATUS"

            if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
                break
            fi

            sleep 5
        done

        echo
        echo "7. Get transcription..."
        curl -s "${BASE_URL}/api/videos/${VIDEO_ID}/transcription" | jq .
    fi
else
    echo "4. Skipping upload test (no video file provided)"
    echo "   Usage: ./test_api.sh path/to/video.mp4"
fi

echo
echo "Done!"
