#!/usr/bin/env python
"""
Test script to diagnose Meta API connection issues
"""
import requests
from src.config import Config

def test_token():
    """Test if the access token is valid"""
    print("=" * 60)
    print("Testing Meta API Access Token")
    print("=" * 60)

    # Test 1: Check token validity with debug endpoint
    print("\n1. Testing token validity...")
    url = f"{Config.FB_BASE_URL}/debug_token"
    params = {
        'input_token': Config.FB_ACCESS_TOKEN,
        'access_token': Config.FB_ACCESS_TOKEN
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Token is valid: {data.get('data', {}).get('is_valid', False)}")
            print(f"   App ID: {data.get('data', {}).get('app_id', 'N/A')}")
            print(f"   User ID: {data.get('data', {}).get('user_id', 'N/A')}")
            print(f"   Expires: {data.get('data', {}).get('expires_at', 'Never')}")
            print(f"   Scopes: {', '.join(data.get('data', {}).get('scopes', []))}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Try simpler API endpoint
    print("\n2. Testing basic Graph API access...")
    url = f"{Config.FB_BASE_URL}/me"
    params = {
        'access_token': Config.FB_ACCESS_TOKEN,
        'fields': 'id,name'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   User ID: {data.get('id', 'N/A')}")
            print(f"   User Name: {data.get('name', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Try ads_archive endpoint with minimal params
    print("\n3. Testing ads_archive endpoint...")
    url = f"{Config.FB_BASE_URL}/ads_archive"
    params = {
        'access_token': Config.FB_ACCESS_TOKEN,
        'search_terms': 'facebook',
        'ad_reached_countries': 'US',
        'fields': 'id,ad_creative_bodies',
        'limit': 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ ads_archive endpoint is working!")
            print(f"   Found {len(data.get('data', []))} ads")
        else:
            print(f"   Error: {response.text}")

            # Try to parse error message
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                error_code = error_data.get('error', {}).get('code', 'N/A')
                print(f"   Error Code: {error_code}")
                print(f"   Error Message: {error_msg}")
            except:
                pass
    except Exception as e:
        print(f"   Error: {e}")

    # Test 4: Check API version
    print("\n4. Checking API version compatibility...")
    print(f"   Current API version: {Config.FB_API_VERSION}")
    print(f"   Recommended: Use latest version (v19.0 or v20.0)")
    print(f"   Note: You can check available versions at:")
    print(f"   https://developers.facebook.com/docs/graph-api/changelog/")

    # Suggestions
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    print("""
1. Check Token Permissions:
   - Go to: https://developers.facebook.com/tools/explorer/
   - Make sure you have these permissions:
     • ads_read
     • pages_read_engagement

2. Verify Token Type:
   - User Access Token (recommended)
   - Should have 60-day expiration

3. Update API Version:
   - Try v19.0 or v20.0 in src/config.py
   - Change: FB_API_VERSION = 'v20.0'

4. Generate New Token:
   - If token is invalid or expired
   - Use Graph API Explorer to generate new one

5. Check App Settings:
   - App must be in "Live" mode (not Development)
   - Marketing API must be enabled
""")

if __name__ == '__main__':
    test_token()
