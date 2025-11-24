"""
Create a test user for development.

This script creates a test user directly in Supabase that can be used
for development and testing without email confirmation.

Usage:
    cd backend
    uv run --env-file .env python scripts/create_test_user.py
"""

import asyncio
import httpx
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from loguru import logger

# Test user credentials
TEST_USER_EMAIL = "testuser@notetaker.dev"
TEST_USER_PASSWORD = "testpass123"


async def create_test_user():
    """Create a test user in Supabase using regular signup."""

    # Supabase regular signup endpoint
    url = f"{settings.supabase_url}/auth/v1/signup"

    headers = {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }

    payload = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Creating test user: {TEST_USER_EMAIL}")
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200 or response.status_code == 201:
                user_data = response.json()
                logger.success("✅ Test user created successfully!")
                logger.info(f"   Email: {TEST_USER_EMAIL}")
                logger.info(f"   Password: {TEST_USER_PASSWORD}")
                if 'user' in user_data:
                    logger.info(f"   User ID: {user_data['user'].get('id')}")
                logger.info("")
                logger.info("   ⚠️  Note: Email confirmation may be required.")
                logger.info("   Check Supabase Dashboard → Authentication → Settings")
                logger.info("   to disable 'Enable email confirmations' for development.")
                return user_data
            elif response.status_code == 400 or response.status_code == 422:
                # User might already exist
                error_msg = response.json().get('msg', response.json().get('error_description', 'Unknown error'))
                if 'already registered' in error_msg.lower() or 'already exists' in error_msg.lower():
                    logger.warning(f"⚠️  User already exists")
                    logger.info("   Trying to sign in with existing credentials...")
                    return await sign_in_test_user()
                else:
                    logger.error(f"❌ Failed to create user: {error_msg}")
                    return None
            else:
                logger.error(f"❌ Failed to create user: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating test user: {str(e)}")
            return None


async def sign_in_test_user():
    """Sign in with test user credentials to verify they work."""

    url = f"{settings.supabase_url}/auth/v1/token?grant_type=password"

    headers = {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }

    payload = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                logger.success("✅ Test user credentials verified!")
                logger.info(f"   Email: {TEST_USER_EMAIL}")
                logger.info(f"   Password: {TEST_USER_PASSWORD}")
                logger.info(f"   Access token: {data.get('access_token')[:50]}...")
                return data
            else:
                logger.error(f"❌ Failed to sign in: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error signing in: {str(e)}")
            return None


async def main():
    """Main function."""
    print("\n" + "="*60)
    print("Creating Test User for Development")
    print("="*60 + "\n")

    # Create or verify test user
    user_data = await create_test_user()

    if user_data:
        print("\n" + "="*60)
        print("✅ TEST USER READY")
        print("="*60)
        print(f"\nYou can now sign in with these credentials:")
        print(f"  📧 Email:    {TEST_USER_EMAIL}")
        print(f"  🔑 Password: {TEST_USER_PASSWORD}")
        print(f"\nVisit http://localhost:3000 and sign in!\n")
    else:
        print("\n" + "="*60)
        print("❌ FAILED TO CREATE TEST USER")
        print("="*60)
        print("\nPlease check:")
        print("  1. Supabase credentials in .env are correct")
        print("  2. Supabase project is active")
        print("  3. Email confirmation is disabled in Supabase Dashboard\n")


if __name__ == "__main__":
    asyncio.run(main())
