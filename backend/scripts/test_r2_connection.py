#!/usr/bin/env python3
"""
Simple R2 connection test to diagnose issues
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import sys

# Hardcoded values for testing
ENDPOINT = "https://0b078b76488bd8482030576f1d0b63d6.r2.cloudflarestorage.com"
BUCKET = "notetaker"
ACCESS_KEY = "d23be321466e903d6ab0ddaf77dd5583"
SECRET_KEY = "168b62212e6177b27735a84fc8c385e09b237c97b1f88ec04b286efd38f32139"

print(f"Testing R2 connection...")
print(f"Endpoint: {ENDPOINT}")
print(f"Bucket: {BUCKET}")
print(f"Access Key: {ACCESS_KEY[:10]}...")
print()

# Create client with aggressive timeout
config = Config(
    connect_timeout=5,
    read_timeout=10,
    retries={'max_attempts': 1}
)

try:
    print("Creating boto3 client...")
    client = boto3.client(
        's3',
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name='auto',
        config=config
    )
    print("✅ Client created")

    print("\nAttempting list_objects_v2 with MaxKeys=1...")
    response = client.list_objects_v2(Bucket=BUCKET, MaxKeys=1)
    print(f"✅ SUCCESS! Response received")
    print(f"   KeyCount: {response.get('KeyCount', 0)}")
    if 'Contents' in response:
        print(f"   First object: {response['Contents'][0]['Key']}")
    else:
        print(f"   Bucket is empty")

    sys.exit(0)

except ClientError as e:
    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
    error_msg = e.response.get('Error', {}).get('Message', 'Unknown')
    print(f"❌ ClientError [{error_code}]: {error_msg}")
    sys.exit(1)

except Exception as e:
    print(f"❌ Exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
