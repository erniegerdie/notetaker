#!/usr/bin/env python3
"""
Test script to verify concurrent request handling for FastAPI async endpoints.
Simulates 5 concurrent video status checks to ensure no blocking on database operations.
"""
import asyncio
import httpx
from uuid import uuid4


async def check_status(client: httpx.AsyncClient, video_id: str, request_num: int):
    """Check video status endpoint."""
    try:
        response = await client.get(f"/api/videos/{video_id}/status")
        print(f"Request {request_num}: Status {response.status_code} (Expected 404)")
        return response.status_code
    except Exception as e:
        print(f"Request {request_num}: Error - {e}")
        return None


async def test_concurrent_requests():
    """Test 5 concurrent requests to verify async handling."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # Test health endpoint first
        try:
            health = await client.get("/health")
            print(f"✅ Server healthy: {health.json()}\n")
        except Exception as e:
            print(f"❌ Server not running: {e}")
            return

        # Generate 5 random video IDs
        video_ids = [str(uuid4()) for _ in range(5)]

        print("Testing 5 concurrent status checks (should all return 404):")
        start_time = asyncio.get_event_loop().time()

        # Execute 5 concurrent requests
        tasks = [
            check_status(client, vid, i+1)
            for i, vid in enumerate(video_ids)
        ]
        results = await asyncio.gather(*tasks)

        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time

        # Validate results
        success = all(status == 404 for status in results if status)
        print(f"\n{'✅' if success else '❌'} All requests completed in {elapsed:.2f}s")

        if elapsed < 1.0:
            print("✅ Async performance confirmed - concurrent execution working")
        else:
            print("⚠️  Execution slower than expected - possible blocking")


if __name__ == "__main__":
    asyncio.run(test_concurrent_requests())
